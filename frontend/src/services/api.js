import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("parakh_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("parakh_token");
    }
    return Promise.reject(error);
  }
);

export const login = (email, password) => api.post("/auth/login", { email, password });
export const getMe = () => api.get("/auth/me");

export const getAssessmentStatus = () => api.get("/assessment/status");
export const getNextQuestion = (mode) => api.get(`/assessment/next/${mode}`);
export const submitAnswer = (payload) => api.post("/assessment/submit", payload);

export const getStudentAnalytics = () => api.get("/analytics/student");
export const getRecentAttempts = () => api.get("/analytics/recent");
export const getAdminAnalytics = () => api.get("/analytics/admin");

export const getQuestions = () => api.get("/questions");
export const addQuestion = (payload) => api.post("/questions", payload);
export const deleteQuestion = (id) => api.delete(`/questions/${id}`);

export const getStudents = () => api.get("/admin/students");
export const createStudent = (payload) => api.post("/admin/students", payload);
export const resetStudent = (id) => api.post(`/admin/students/${id}/reset`);
export const deleteStudent = (id) => api.delete(`/admin/students/${id}`);

export default api;
