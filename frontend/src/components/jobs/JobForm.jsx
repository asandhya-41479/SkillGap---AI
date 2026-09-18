import { useState } from 'react';

export default function JobForm({ onSubmit, submitting }) {
  const [form, setForm] = useState({ title: '', target_role: '', raw_description: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
    setForm({ title: '', target_role: '', raw_description: '' });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-4 rounded-lg shadow space-y-3">
      <div>
        <label className="block text-sm text-gray-600">Title (optional)</label>
        <input
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          className="border rounded px-3 py-2 w-full"
          placeholder="e.g. Google AI Engineer posting"
        />
      </div>
      <div>
        <label className="block text-sm text-gray-600">Target Role</label>
        <input
          required
          value={form.target_role}
          onChange={(e) => setForm({ ...form, target_role: e.target.value })}
          className="border rounded px-3 py-2 w-full"
          placeholder="e.g. AI Engineer"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-600">Job Description</label>
        <textarea
          required
          minLength={50}
          rows={6}
          value={form.raw_description}
          onChange={(e) => setForm({ ...form, raw_description: e.target.value })}
          className="border rounded px-3 py-2 w-full"
          placeholder="Paste the full job description here (minimum 50 characters)..."
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? 'Submitting...' : 'Submit Job Description'}
      </button>
    </form>
  );
}