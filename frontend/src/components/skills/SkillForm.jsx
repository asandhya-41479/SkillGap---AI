import { useState, useEffect } from 'react';

const CATEGORIES = ['programming_language', 'framework', 'database', 'ai_ml', 'cloud', 'devops', 'tool', 'other'];
const LEVELS = ['beginner', 'intermediate', 'advanced'];
export const CATEGORY_LABEL = {
  programming_language: 'Language', framework: 'Framework', database: 'Database', ai_ml: 'AI / ML',
  cloud: 'Cloud', devops: 'DevOps', tool: 'Tool', other: 'Other',
};

const selectCls = 'h-11 w-full rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm text-ink focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand-soft';

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
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4">
      <h2 className="m-0 font-display text-lg font-bold">{editingSkill ? `Edit ${editingSkill.skill_name}` : 'Add a skill'}</h2>
      {!editingSkill && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="sk-name" className="field-label">Skill name</label>
          <input id="sk-name" required value={form.skill_name} maxLength={100}
            onChange={(e) => setForm({ ...form, skill_name: e.target.value })}
            className={selectCls} placeholder="e.g. React" />
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="sk-cat" className="field-label">Category</label>
          <select id="sk-cat" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className={selectCls}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABEL[c]}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="sk-lvl" className="field-label">Level</label>
          <select id="sk-lvl" value={form.self_assessed_level} onChange={(e) => setForm({ ...form, self_assessed_level: e.target.value })} className={`${selectCls} capitalize`}>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      </div>
      <div className="flex gap-2">
        <button type="submit" className="btn-primary">{editingSkill ? 'Save changes' : 'Add skill'}</button>
        {editingSkill && <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>}
      </div>
    </form>
  );
}
