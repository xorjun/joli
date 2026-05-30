import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const de = {
  app: { name: "Joli", tagline: "KI-Karriere-Concierge" },
  auth: {
    login: "Anmelden",
    register: "Registrieren",
    email: "E-Mail",
    password: "Passwort",
    loginBtn: "Anmelden",
    registerBtn: "Konto erstellen",
    noAccount: "Noch kein Konto?",
    hasAccount: "Bereits registriert?",
    logout: "Abmelden",
  },
  chat: {
    placeholder: "Nachricht schreiben... oder Job-URL einfügen",
    newChat: "Neuer Chat",
    send: "Senden",
    typing: "schreibt...",
  },
  profile: {
    completeness: "Profilvollständigkeit",
    personalData: "Persönliche Daten",
    workExperience: "Berufserfahrung",
    education: "Ausbildung",
    skills: "Kenntnisse",
    languages: "Sprachen",
    certificates: "Zertifikate",
    zeugnisse: "Zeugnisse",
    salary: "Gehaltsvorstellung",
    notice: "Kündigungsfrist",
  },
  documents: {
    generateResume: "Lebenslauf erstellen",
    generateLetter: "Anschreiben erstellen",
    downloadDOCX: "DOCX herunterladen",
    downloadPDF: "PDF herunterladen",
    compliance: "DIN 5008",
    compliant: "DIN 5008 konform",
    warnings: "Warnungen",
  },
};

const en: typeof de = {
  app: { name: "Joli", tagline: "AI Career Concierge" },
  auth: {
    login: "Login",
    register: "Register",
    email: "Email",
    password: "Password",
    loginBtn: "Sign In",
    registerBtn: "Create Account",
    noAccount: "Don't have an account?",
    hasAccount: "Already have an account?",
    logout: "Logout",
  },
  chat: {
    placeholder: "Type a message... or paste a job URL",
    newChat: "New Chat",
    send: "Send",
    typing: "typing...",
  },
  profile: {
    completeness: "Profile Completeness",
    personalData: "Personal Data",
    workExperience: "Work Experience",
    education: "Education",
    skills: "Skills",
    languages: "Languages",
    certificates: "Certificates",
    zeugnisse: "References",
    salary: "Salary Expectation",
    notice: "Notice Period",
  },
  documents: {
    generateResume: "Generate Resume",
    generateLetter: "Generate Cover Letter",
    downloadDOCX: "Download DOCX",
    downloadPDF: "Download PDF",
    compliance: "DIN 5008",
    compliant: "DIN 5008 Compliant",
    warnings: "Warnings",
  },
};

i18n.use(initReactI18next).init({
  resources: { de: { translation: de }, en: { translation: en } },
  lng: "de",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
