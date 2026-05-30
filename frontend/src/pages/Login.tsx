import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { motion } from "framer-motion";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden p-4 md:p-8">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-24 -left-24 h-64 w-64 rounded-full bg-[#ff6b4a]/25 blur-3xl" />
        <div className="absolute top-[16%] right-[-6rem] h-80 w-80 rounded-full bg-[#0f8b8d]/20 blur-3xl" />
        <div className="absolute bottom-[-8rem] left-[28%] h-72 w-72 rounded-full bg-[#ffd166]/25 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-full max-w-5xl items-center"
      >
        <div className="grid w-full gap-6 rounded-3xl border border-white/60 bg-white/60 p-4 shadow-[0_30px_90px_rgba(17,24,39,0.18)] backdrop-blur-xl md:grid-cols-[1.1fr_0.9fr] md:p-6">
          <div className="hidden rounded-2xl bg-gradient-to-br from-[#1f2937] via-[#0f8b8d] to-[#1f2937] p-8 text-white md:flex md:flex-col md:justify-between">
            <div>
              <p className="mb-4 inline-flex rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white/90">
                Career OS
              </p>
              <h1 className="text-4xl font-bold leading-tight">Find the role. Win the interview.</h1>
              <p className="mt-4 max-w-sm text-sm text-white/80">
                Joli turns each job post into a focused strategy, tailored resume bullets, and a cover letter that sounds like you.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl bg-white/15 p-3">
                <p className="text-2xl font-bold">24/7</p>
                <p className="text-white/70">AI coaching</p>
              </div>
              <div className="rounded-xl bg-white/15 p-3">
                <p className="text-2xl font-bold">DIN</p>
                <p className="text-white/70">format aware</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-white/80 p-6 md:p-8">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-slate-800">Welcome back</h2>
              <p className="mt-2 text-sm text-slate-500">Sign in to continue building your next application.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-600">Email</span>
                <input
                  type="email"
                  placeholder="you@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 placeholder-slate-400 outline-none transition focus:border-[#0f8b8d] focus:ring-2 focus:ring-[#0f8b8d]/20"
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-600">Password</span>
                <input
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 placeholder-slate-400 outline-none transition focus:border-[#0f8b8d] focus:ring-2 focus:ring-[#0f8b8d]/20"
                />
              </label>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              New here?{" "}
              <Link to="/register" className="font-semibold text-[#0f8b8d] hover:text-[#0d7c7d]">
                Create account
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
