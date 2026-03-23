import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1"
});

export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return API.post("/upload/", formData);
};

export const approveField = (id, field) => {
  return API.post(`/review/approve/${id}/${field}`);
};

export const rejectField = (id, field) => {
  return API.post(`/review/reject/${id}/${field}`);
};