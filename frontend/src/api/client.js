const BASE_URL = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Request failed");
  }
  return res.json();
}

// Tasks
export const getTasks = (sellerId, params = {}) => {
  const qs = new URLSearchParams({ seller_id: sellerId, ...params }).toString();
  return request(`/tasks?${qs}`);
};

export const getTask = (taskId) => request(`/tasks/${taskId}`);

export const updateTaskStatus = (taskId, status, notes) =>
  request(`/tasks/${taskId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status, notes }),
  });

// Companies
export const getCompanySnapshot = (companyId) =>
  request(`/companies/${companyId}/snapshot`);

export const getCompanyISVs = (companyId) =>
  request(`/companies/${companyId}/isvs`);

// Contacts
export const getContacts = (companyId) =>
  request(`/contacts/${companyId}`);

// Coaching
export const getCoachingHistory = (sellerId) =>
  request(`/coaching/${sellerId}`);

export const startRoleplay = (sellerId, taskId) =>
  request("/coaching/roleplay/start", {
    method: "POST",
    body: JSON.stringify({ seller_id: sellerId, task_id: taskId }),
  });

// Config
export const getPlatform = () => request("/config/platform");

export const updatePlatform = (vendor) =>
  request("/config/platform", {
    method: "PUT",
    body: JSON.stringify({ vendor }),
  });
