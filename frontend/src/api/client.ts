import axios from "axios";

const API_BASE = "/api";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("joli_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("joli_token");
      localStorage.removeItem("joli_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// Auth
export const register = (email: string, password: string, uiLanguage: string) =>
  client.post("/auth/register", { email, password, ui_language: uiLanguage });

export const login = (email: string, password: string) =>
  client.post("/auth/login", { email, password });

export const getMe = () => client.get("/auth/me");

// Profile
export const getProfile = () => client.get("/profile/me");
export const updateProfile = (data: Record<string, unknown>) =>
  client.put("/profile/me", data);
export const uploadPhoto = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return client.post("/profile/photo", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// Chat
export const listSessions = () => client.get("/chat/sessions");
export const createSession = () => client.post("/chat/sessions");
export const getMessages = (sessionId: string) =>
  client.get(`/chat/sessions/${sessionId}`);
export const sendMessage = (sessionId: string, content: string) =>
  client.post(`/chat/sessions/${sessionId}/messages`, { content });

// Jobs
export const scrapeJob = (url: string) => client.post("/jobs/scrape", { url });
export const getJob = (jobId: string) => client.get(`/jobs/${jobId}`);

// Documents
export const generateDocument = (
  applicationId: string,
  docType: string,
  language: string
) => client.post("/documents/generate", { application_id: applicationId, doc_type: docType, language });
export const getDocument = (docId: string) => client.get(`/documents/${docId}`);
export const getCompliance = (docId: string) =>
  client.get(`/documents/${docId}/compliance`);

// Zeugnisse
export const listZeugnisse = () => client.get("/zeugnisse");
export const uploadZeugnis = (file: File, title: string, issuer: string, date: string) => {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("issuer", issuer);
  form.append("date", date);
  return client.post("/zeugnisse", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const decodeZeugnis = (zeugnisId: string, text: string) =>
  client.post(`/zeugnisse/${zeugnisId}/decode`, { zeugnis_text: text });

export default client;
