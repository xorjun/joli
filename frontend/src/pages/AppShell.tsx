import { useState, useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  listSessions,
  createSession,
  getMessages,
  sendMessage,
  getProfile,
  scrapeJob,
  generateDocument,
} from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  message_type: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

interface Session {
  id: string;
  title: string;
  message_count: number;
  updated_at: string;
}

export default function AppShell() {
  const { user, logout } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [profileCompleteness, setProfileCompleteness] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
    loadProfile();
  }, []);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadProfile = async () => {
    try {
      const res = await getProfile();
      setProfileCompleteness(res.data.profile_completeness || 0);
    } catch {
      // Profile not created yet
    }
  };

  const loadSessions = async () => {
    try {
      const res = await listSessions();
      setSessions(res.data);
    } catch {
      // No sessions yet
    }
  };

  const selectSession = async (session: Session) => {
    setActiveSession(session);
    try {
      const res = await getMessages(session.id);
      setMessages(res.data);
    } catch {
      setMessages([]);
    }
  };

  const newChat = async () => {
    try {
      const res = await createSession();
      setActiveSession(res.data);
      setMessages([]);
      loadSessions();
    } catch {
      // Failed
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    let session = activeSession;
    if (!session) {
      try {
        const res = await createSession();
        session = res.data;
        setActiveSession(session);
        loadSessions();
      } catch {
        return;
      }
    }

    const userMsg: Message = {
      id: "temp-" + Date.now(),
      role: "user",
      content: input,
      message_type: "chat",
      metadata_json: {},
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessage(session.id, input);

      // Update profile completeness from metadata
      const metadata = res.data.metadata_json || {};
      if (metadata.profile_completeness !== undefined) {
        setProfileCompleteness(metadata.profile_completeness);
      }

      setMessages((prev) => [...prev, res.data]);

      // Handle job URL detection
      if (metadata.detected_job_url) {
        // Auto-scrape
        setTimeout(async () => {
          try {
            const jobRes = await scrapeJob(metadata.detected_job_url as string);
            const jobMsg: Message = {
              id: "job-" + Date.now(),
              role: "assistant",
              content: `## Stellenanalyse: ${jobRes.data.job_title}\n\n**${jobRes.data.company}** — ${jobRes.data.company_location}\n\n${(jobRes.data.job_description_raw || "").slice(0, 500)}...`,
              message_type: "job_analysis",
              metadata_json: { job_id: jobRes.data.id, ...jobRes.data },
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, jobMsg]);
          } catch {
            // Scrape failed silently
          }
        }, 500);
      }
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setLoading(false);
      loadSessions();
    }
  };

  const handleGenerateDocument = async (jobId: string, docType: string) => {
    setLoading(true);
    try {
      const res = await generateDocument(jobId, docType, "de");
      const docMsg: Message = {
        id: "doc-" + Date.now(),
        role: "assistant",
        content: res.data.markdown_content,
        message_type: "document_card",
        metadata_json: {
          document_id: res.data.id,
          doc_type: res.data.doc_type,
          docx_path: res.data.docx_path,
          pdf_path: res.data.pdf_path,
        },
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, docMsg]);
    } catch {
      // Failed
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Extract visible content from AI messages
  const getVisibleContent = (msg: Message) => {
    if (msg.metadata_json?.visible_content) {
      return msg.metadata_json.visible_content as string;
    }
    return msg.content;
  };

  // Simple markdown-to-html for rendering
  const renderContent = (content: string) => {
    let html = content
      .replace(/### (.+)/g, '<h3 class="text-sm font-bold text-indigo-300 mt-3 mb-1">$1</h3>')
      .replace(/## (.+)/g, '<h2 class="text-base font-bold text-indigo-200 mt-4 mb-2">$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
      .replace(/\n- (.+)/g, '\n<span class="flex gap-2"><span class="text-indigo-400">•</span> $1</span>')
      .replace(/\n/g, "<br/>");
    return html;
  };

  return (
    <div className="h-screen flex bg-slate-950 text-white overflow-hidden">
      {/* Animated background orbs */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 right-0 w-[50vw] h-[50vw] bg-indigo-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-[40vw] h-[40vw] bg-violet-600/10 rounded-full blur-[100px]" />
      </div>

      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="w-64 backdrop-blur-xl bg-slate-900/80 border-r border-white/5 flex flex-col z-10 shrink-0"
          >
            <div className="p-4 border-b border-white/5">
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                Joli
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-slate-500">{user?.email}</span>
              </div>
            </div>

            <button
              onClick={newChat}
              className="mx-3 mt-3 px-4 py-2 mb-2 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/30 rounded-lg text-sm transition-all flex items-center gap-2"
            >
              <span>+</span> Neuer Chat
            </button>

            <div className="flex-1 overflow-y-auto px-2">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSession(s)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 transition-all truncate ${
                    activeSession?.id === s.id
                      ? "bg-indigo-500/20 text-white"
                      : "text-slate-400 hover:bg-white/5"
                  }`}
                >
                  {s.title}
                </button>
              ))}
            </div>

            {/* Profile completeness */}
            <div className="p-4 border-t border-white/5">
              <div className="text-xs text-slate-500 mb-1">Profilvollständigkeit</div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-indigo-500 to-violet-500"
                  animate={{ width: `${profileCompleteness}%` }}
                  transition={{ duration: 0.8 }}
                />
              </div>
              <div className="text-xs text-slate-500 mt-1">{profileCompleteness}%</div>
            </div>

            <button
              onClick={logout}
              className="m-3 px-4 py-2 text-sm text-slate-500 hover:text-white hover:bg-white/5 rounded-lg transition-all text-left"
            >
              Abmelden
            </button>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Top bar */}
        <header className="h-14 backdrop-blur-xl bg-slate-900/60 border-b border-white/5 flex items-center px-4 shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-slate-400 hover:text-white transition-colors mr-3"
          >
            ☰
          </button>
          <span className="text-sm text-slate-400 truncate">
            {activeSession?.title || "Joli — KI-Karriere-Concierge"}
          </span>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", delay: 0.2 }}
                  className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-3xl"
                >
                  ✨
                </motion.div>
                <h2 className="text-xl font-semibold mb-2">Willkommen bei Joli</h2>
                <p className="text-slate-400 max-w-md">
                  Ich bin Ihr KI-Karriere-Coach. Erzählen Sie mir von Ihrer beruflichen Laufbahn,
                  oder fügen Sie einfach eine Stellenanzeige ein — ich helfe Ihnen bei der perfekten Bewerbung.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-indigo-500/30 border border-indigo-500/30"
                    : "bg-white/5 border border-white/10"
                }`}
              >
                {msg.message_type === "document_card" ? (
                  <div>
                    <div
                      className="text-sm leading-relaxed prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: renderContent(getVisibleContent(msg)) }}
                    />
                    <div className="flex gap-2 mt-3 pt-3 border-t border-white/10">
                      {msg.metadata_json?.docx_path && (
                        <a
                          href={`/api/documents/${msg.metadata_json.document_id}/docx`}
                          className="px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg text-xs transition-colors"
                          target="_blank"
                          rel="noreferrer"
                        >
                          📄 DOCX
                        </a>
                      )}
                      {msg.metadata_json?.pdf_path && (
                        <a
                          href={`/api/documents/${msg.metadata_json.document_id}/pdf`}
                          className="px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg text-xs transition-colors"
                          target="_blank"
                          rel="noreferrer"
                        >
                          📑 PDF
                        </a>
                      )}
                    </div>
                  </div>
                ) : msg.message_type === "job_analysis" ? (
                  <div>
                    <div
                      className="text-sm leading-relaxed prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: renderContent(getVisibleContent(msg)) }}
                    />
                    {msg.metadata_json?.job_id && (
                      <div className="flex gap-2 mt-3 pt-3 border-t border-white/10">
                        <button
                          onClick={() =>
                            handleGenerateDocument(
                              msg.metadata_json?.job_id as string,
                              "resume"
                            )
                          }
                          className="px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg text-xs transition-colors"
                        >
                          📝 Lebenslauf erstellen
                        </button>
                        <button
                          onClick={() =>
                            handleGenerateDocument(
                              msg.metadata_json?.job_id as string,
                              "cover_letter"
                            )
                          }
                          className="px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg text-xs transition-colors"
                        >
                          ✉️ Anschreiben
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    className="text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{
                      __html: renderContent(getVisibleContent(msg)),
                    }}
                  />
                )}
              </div>
            </motion.div>
          ))}

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }} />
                  <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEnd} />
        </div>

        {/* Input */}
        <div className="p-4 backdrop-blur-xl bg-slate-900/60 border-t border-white/5">
          <div className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nachricht schreiben... oder Job-URL einfügen"
              disabled={loading}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-colors disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-400 hover:to-violet-400 disabled:from-slate-700 disabled:to-slate-700 text-white rounded-xl px-5 py-3 text-sm font-medium transition-all disabled:cursor-not-allowed"
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
