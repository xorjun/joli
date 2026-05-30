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

    if (!session) {
      setLoading(false);
      return;
    }

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
      const res = await generateDocument(jobId, docType, "en");
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

  const quickPrompts = [
    "Analyze this role for me",
    "Extract my strongest fit points",
    "Create a resume draft for this job",
  ];

  return (
    <div className="relative h-screen overflow-hidden bg-transparent text-slate-800">
      <div className="pointer-events-none absolute inset-0 z-0">
        <div className="absolute left-[-5rem] top-[-4rem] h-72 w-72 rounded-full bg-[#ff6b4a]/15 blur-3xl" />
        <div className="absolute bottom-[-6rem] right-[-2rem] h-80 w-80 rounded-full bg-[#0f8b8d]/20 blur-3xl" />
      </div>

      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="z-10 flex w-72 shrink-0 flex-col border-r border-slate-200/70 bg-white/70 backdrop-blur-xl"
          >
            <div className="border-b border-slate-200/80 p-5">
              <h1 className="text-2xl font-bold text-slate-800">
                Joli
              </h1>
              <p className="mt-1 text-xs text-slate-500">{user?.email}</p>
              <div className="mt-3 inline-flex rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                Career Concierge
              </div>
            </div>

            <button
              onClick={newChat}
              className="mx-4 mt-4 mb-3 rounded-xl bg-slate-900 px-4 py-3 text-left text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              + New conversation
            </button>

            <div className="flex-1 overflow-y-auto px-3">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSession(s)}
                  className={`mb-1 w-full truncate rounded-xl px-3 py-2.5 text-left text-sm transition ${
                    activeSession?.id === s.id
                      ? "bg-[#0f8b8d]/15 font-semibold text-slate-800"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {s.title}
                </button>
              ))}
            </div>

            <div className="border-t border-slate-200/80 p-4">
              <div className="mb-1 text-xs text-slate-500">Profile completeness</div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <motion.div
                  className="h-full bg-gradient-to-r from-[#ff6b4a] to-[#0f8b8d]"
                  animate={{ width: `${profileCompleteness}%` }}
                  transition={{ duration: 0.8 }}
                />
              </div>
              <div className="mt-1 text-xs text-slate-500">{profileCompleteness}%</div>
            </div>

            <button
              onClick={logout}
              className="m-3 rounded-xl px-4 py-2 text-left text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            >
              Log out
            </button>
          </motion.aside>
        )}
      </AnimatePresence>

      <div className="relative z-10 flex flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center border-b border-slate-200/70 bg-white/70 px-4 backdrop-blur-xl md:px-6">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="mr-3 rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
          >
            ☰
          </button>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-700">
              {activeSession?.title || "Joli Workspace"}
            </p>
            <p className="truncate text-xs text-slate-500">Chat-driven applications, tailored in minutes</p>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-5 md:px-8">
          <div className="mx-auto w-full max-w-4xl space-y-4">
          {messages.length === 0 && !loading && (
            <div className="flex min-h-[52vh] items-center justify-center">
              <div className="text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", delay: 0.2 }}
                  className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ff6b4a] to-[#0f8b8d] text-3xl text-white"
                >
                  ✨
                </motion.div>
                <h2 className="mb-2 text-2xl font-bold text-slate-800">Welcome to Joli</h2>
                <p className="mx-auto max-w-xl text-slate-600">
                  Paste a job post, share your background, and let Joli create your interview-ready application package.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {quickPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => setInput(prompt)}
                      className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-600 transition hover:border-[#0f8b8d] hover:text-[#0f8b8d]"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            (() => {
              const docxPath = typeof msg.metadata_json?.docx_path === "string" ? msg.metadata_json.docx_path : "";
              const pdfPath = typeof msg.metadata_json?.pdf_path === "string" ? msg.metadata_json.pdf_path : "";
              const jobId = typeof msg.metadata_json?.job_id === "string" ? msg.metadata_json.job_id : "";
              return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[82%] rounded-2xl px-4 py-3 shadow-sm md:max-w-[75%] ${
                  msg.role === "user"
                    ? "border border-[#0f8b8d]/30 bg-[#0f8b8d]/12 text-slate-800"
                    : "border border-slate-200 bg-white text-slate-700"
                }`}
              >
                {msg.message_type === "document_card" ? (
                  <div>
                    <div
                      className="max-w-none text-sm leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: renderContent(getVisibleContent(msg)) }}
                    />
                    <div className="mt-3 flex gap-2 border-t border-slate-200 pt-3">
                      {docxPath && (
                        <a
                          href={`/api/documents/${msg.metadata_json.document_id}/docx`}
                          className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-200"
                          target="_blank"
                          rel="noreferrer"
                        >
                          DOCX
                        </a>
                      )}
                      {pdfPath && (
                        <a
                          href={`/api/documents/${msg.metadata_json.document_id}/pdf`}
                          className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-200"
                          target="_blank"
                          rel="noreferrer"
                        >
                          PDF
                        </a>
                      )}
                    </div>
                  </div>
                ) : msg.message_type === "job_analysis" ? (
                  <div>
                    <div
                      className="max-w-none text-sm leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: renderContent(getVisibleContent(msg)) }}
                    />
                    {jobId && (
                      <div className="mt-3 flex gap-2 border-t border-slate-200 pt-3">
                        <button
                          onClick={() =>
                            handleGenerateDocument(
                              jobId,
                              "resume"
                            )
                          }
                          className="rounded-lg bg-[#0f8b8d] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-[#0d7c7d]"
                        >
                          Generate Resume
                        </button>
                        <button
                          onClick={() =>
                            handleGenerateDocument(
                              jobId,
                              "cover_letter"
                            )
                          }
                          className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
                        >
                          Cover Letter
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
              );
            })()
          ))}

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[#0f8b8d]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[#0f8b8d]" style={{ animationDelay: "0.15s" }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[#0f8b8d]" style={{ animationDelay: "0.3s" }} />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEnd} />
          </div>
        </div>

        <div className="border-t border-slate-200/80 bg-white/70 p-4 backdrop-blur-xl md:px-8">
          <div className="mx-auto flex w-full max-w-4xl items-end gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message or paste a job URL"
              disabled={loading}
              className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder-slate-400 outline-none transition focus:border-[#0f8b8d] focus:ring-2 focus:ring-[#0f8b8d]/20 disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
