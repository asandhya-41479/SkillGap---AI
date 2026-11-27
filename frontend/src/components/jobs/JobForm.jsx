import { useState } from 'react';

const inputCls = 'h-11 w-full rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm text-ink placeholder:text-slate-500 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand-soft';

export default function JobForm({ onSubmit, submitting }) {
  const [form, setForm] = useState({ title: '', target_role: '', raw_description: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
    setForm({ title: '', target_role: '', raw_description: '' });
  };

  const len = form.raw_description.length;

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4">
      <div>
        <h2 className="m-0 font-display text-lg font-bold">Add a job description</h2>
        <p className="m-0 mt-1 text-sm text-muted">Paste a real job posting. SkillGap AI extracts every requirement and how important it is.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="jb-role" className="field-label">Target role</label>
          <input id="jb-role" required maxLength={150} value={form.target_role}
            onChange={(e) => setForm({ ...form, target_role: e.target.value })} className={inputCls} placeholder="e.g. Agentic AI Engineer" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="jb-title" className="field-label">Title <span className="font-normal text-muted">(optional)</span></label>
          <input id="jb-title" maxLength={200} value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputCls} placeholder="e.g. Company name or posting title" />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <div className="flex items-baseline justify-between">
          <label htmlFor="jb-desc" className="field-label">Job description</label>
          <span className={`text-xs ${len > 0 && len < 50 ? 'font-semibold text-red-700' : 'text-muted'}`}>{len} characters (minimum 50)</span>
        </div>
        <textarea id="jb-desc" required minLength={50} rows={8} value={form.raw_description}
          onChange={(e) => setForm({ ...form, raw_description: e.target.value })}
          className="w-full resize-y rounded-xl border-[1.5px] border-slate-300 bg-white p-3 text-sm leading-relaxed text-ink placeholder:text-slate-500 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand-soft"
          placeholder="Paste the full job description here…" />
      </div>
      <button type="submit" disabled={submitting} className="btn-primary self-start">{submitting ? 'Saving…' : 'Save job description'}</button>
    </form>
  );
}
