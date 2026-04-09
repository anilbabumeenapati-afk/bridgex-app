import axios from "axios";
import type { AxiosProgressEvent } from "axios";

const API = axios.create({
  baseURL: "https://bridgex-app.onrender.com/api/v1",
});

export const uploadFile = (
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
) => {
  const formData = new FormData();
  formData.append("file", file);

  return API.post("/upload/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress,
    timeout: 120000,
  });
};

export const getEvidence = (id: string | number) =>
  API.get(`/evidence/${id}`);

export const approveField = (id: string | number, field: string) =>
  API.post(`/review/approve/${id}/${field}`);

export const rejectField = (id: string | number, field: string) =>
  API.post(`/review/reject/${id}/${field}`);

export const getDownloadUrl = (filename: string) =>
  `${API.defaults.baseURL}/download/${filename}`;