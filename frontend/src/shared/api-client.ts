// shared/api-client.ts
// Encapsulates HTTP calls to Sync To-Do backend as per docs/api-spec.json

export type Task = {
  id: string;
  title: string;
  completed: boolean;
};

const API_BASE = 'https://project-e506628f-8ee9-434a-9890.onrender.com';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => null);
    const message = error?.message ?? res.statusText;
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

// GET /tasks
export async function getTasks(): Promise<Task[]> {
  const res = await fetch(`${API_BASE}/tasks`, {
    headers: { 'Content-Type': 'application/json' }
  });
  return handleResponse<Task[]>(res);
}

// POST /tasks
export async function createTask(title: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  return handleResponse<Task>(res);
}

// PATCH /tasks/{id}
export async function updateTask(
  id: string,
  data: Partial<Pick<Task, 'title' | 'completed'>>
): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return handleResponse<Task>(res);
}
