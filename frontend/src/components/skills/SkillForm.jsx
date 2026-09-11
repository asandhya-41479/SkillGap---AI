import { useState, useEffect } from 'react';

const CATEGORIES = ['programming_language', 'framework', 'database', 'ai_ml', 'cloud', 'devops', 'tool', 'other'];
const LEVELS = ['beginner', 'intermediate', 'advanced'];

export default function SkillForm({ onSubmit, editingSkill, onCancel }) {
  const [form, setForm] = useState({ skill_name: '', category: 'other', self_assessed_level: 'beginner' });

  useEffect(() => {
    if (editingSkill) {
      setForm({
        skill_name: editingSkill.skill_name,
        category: editingSkill.category,
        self_assessed_level: editingSkill.self_assessed_level || 'beginner',
      });
    }
  }, [editingSkill]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(editingSkill ? { category: form.category, self_assessed_level: form.self_assessed_level } : form);
    if (!editingSkill) setForm({ skill_name: '', category: 'other', self_assessed_level: 'beginner' });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap gap-3 items-end bg-white p-4 rounded-lg shadow">
      {!editingSkill && (
        <div>
          <label className="block text-sm text-gray-600">Skill name</label>
          <input
            required
            value={form.skill_name}
            onChange={(e) => setForm({ ...form, skill_name: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="e.g. React"
          />
        </div>
      )}
      <div>
        <label className="block text-sm text-gray-600">Category</label>
        <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="border rounded px-3 py-2">
          {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-sm text-gray-600">Level</label>
        <select value={form.self_assessed_level} onChange={(e) => setForm({ ...form, self_assessed_level: e.target.value })} className="border rounded px-3 py-2">
          {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
      </div>
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        {editingSkill ? 'Save' : 'Add Skill'}
      </button>
      {editingSkill && (
        <button type="button" onClick={onCancel} className="text-gray-500 px-4 py-2">Cancel</button>
      )}
    </form>
  );
}