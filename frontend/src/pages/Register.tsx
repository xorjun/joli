import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { motion } from "framer-motion";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [uiLanguage, setUiLanguage] = useState("en");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, uiLanguage);
      navigate("/");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden p-4 md:p-8">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-4rem] right-[-4rem] h-72 w-72 rounded-full bg-[#ff6b4a]/20 blur-3xl" />
        <div className="absolute bottom-[-5rem] left-[-3rem] h-72 w-72 rounded-full bg-[#0f8b8d]/20 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-full max-w-4xl items-center"
      >
        <div className="w-full rounded-3xl border border-white/60 bg-white/65 p-6 shadow-[0_30px_90px_rgba(17,24,39,0.18)] backdrop-blur-xl md:p-10">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-slate-800">Create your Joli account</h1>
            <p className="mt-2 text-sm text-slate-500">Set up your profile and start generating job-ready applications.</p>
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
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 placeholder-slate-400 outline-none transition focus:border-[#0f8b8d] focus:ring-2 focus:ring-[#0f8b8d]/20"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-600">Interface language</span>
              <select
                value={uiLanguage}
                onChange={(e) => setUiLanguage(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 outline-none transition focus:border-[#0f8b8d] focus:ring-2 focus:ring-[#0f8b8d]/20"
              >
                <option value="en">English</option>
                <option value="de">German</option>
              </select>
            </label>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-[#0f8b8d] hover:text-[#0d7c7d]">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
