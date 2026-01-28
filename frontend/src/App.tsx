import React, { useEffect, useState } from 'react';
import { getTasks, createTask, updateTask, Task } from './shared/api-client';

// API operations used:
// GET /tasks
// POST /tasks
// PATCH /tasks/{id}
// All HTTP calls are done via shared/api-client

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);

  const loadTasks = async () => {
    try {
      const data = await getTasks();
      setTasks(data.sort((a, b) => (a.id < b.id ? 1 : -1)));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadTasks();
    const intervalId = setInterval(loadTasks, 30000); // poll every 30s
    return () => clearInterval(intervalId);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      const newTask = await createTask(title.trim());
      setTasks(prev => [newTask, ...prev]);
      setTitle('');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleCompleted = async (task: Task) => {
    try {
      const updated = await updateTask(task.id, { completed: !task.completed });
      setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '1rem' }}>
      <h1>Sync To-Do</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={title}
          disabled={loading}
          onChange={e => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          style={{ width: '80%', padding: '0.5rem' }}
        />
        <button type="submit" disabled={loading || !title.trim()}>
          Add
        </button>
      </form>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {tasks.map(task => (
          <li key={task.id} style={{ padding: '0.5rem 0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => toggleCompleted(task)}
              />
              <span style={{ textDecoration: task.completed ? 'line-through' : 'none' }}>
                {task.title}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
