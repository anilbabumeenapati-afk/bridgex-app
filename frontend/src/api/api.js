import axios from "axios";

// ✅ PRODUCTION BACKEND
const API = axios.create({
  baseURL: "https://bridgex-app.onrender.com/api/v1"
});

// ✅ Upload
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return API.post("/upload/", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
};

// ✅ Approve
export const approveField = (id, field) => {
  return API.post(`/review/approve/${id}/${field}`);
};

// ✅ Reject
export const rejectField = (id, field) => {
  return API.post(`/review/reject/${id}/${field}`);
};
console.log("🔥 USING RENDER BACKEND v2");