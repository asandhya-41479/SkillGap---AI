import { useState } from 'react';
import { Link } from 'react-router-dom';
import { STATUS, CLASS_LABEL, IMPORTANCE_LABEL, WEIGHT, statusOf, nameOf, importanceOf } from '../../lib/gap';

// One requirement card: name, how it matched, weight, "any one of" alternatives and the explanation.
export default function ResultRow({ result }) {
  const [showDetails, setShowDetails] = useState(false);
  const st = statusOf(result);
  const imp = importanceOf(result);
  const alts = result.job_requirement?.alternatives || [];

  return (
    <article className="flex flex-col gap-2 rounded-2xl border border-line bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,.05)]">
      <div className="flex items-start justify-between gap-3">
        <h4 className="m-0 font-display text-base font-bold text-ink">{nameOf(result)}</h4>
        <span className={`flex-none rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${STATUS[st].soft}`}>
          {st === 'strong' ? 'Strong' : `${STATUS[st].label.split(' ')[0]}`}
        </span>
      </div>
      <p className="m-0 text-[13px] font-semibold text-muted">
        {IMPORTANCE_LABEL[imp] || imp} ×{WEIGHT[imp]} · {CLASS_LABEL[result.classification]}
      </p>
      {alts.length > 0 && (
        <p className="m-0 rounded-lg bg-slate-50 px-2.5 py-1.5 text-[13px] text-slate-700">
          <span className="font-semibold">Any one of these counts:</span> {alts.join(', ')}
        </p>
      )}
      {result.explanation && <p className="m-0 text-sm leading-relaxed text-slate-700">{result.explanation}</p>}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <button type="button" onClick={() => setShowDetails(!showDetails)}
          className="min-h-9 text-xs font-semibold text-muted hover:text-ink" aria-expanded={showDetails}>
          {showDetails ? 'Hide' : 'Show'} technical details
        </button>
        {st !== 'strong' && (
          <Link to="/roadmap" className="rounded-lg bg-brand-soft px-3 py-2 text-xs font-bold text-brand-dark hover:bg-blue-200">
            Plan it in Roadmap →
          </Link>
        )}
      </div>
      {showDetails && (
        <p className="m-0 text-xs text-muted">
          Similarity: {result.similarity_score ?? 'n/a'} · Method: {result.match_method} · Explanation: {result.explanation_source}
        </p>
      )}
    </article>
  );
}
