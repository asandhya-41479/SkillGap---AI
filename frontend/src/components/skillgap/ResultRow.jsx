import { useState } from 'react';

const STATUS_ICON = { strong: '✓', partial: '◐', transferable: '↗', gap: '⚠' };
const STATUS_LABEL = { strong: 'Strong Match', partial: 'Partial Match', transferable: 'Transferable', gap: 'Gap' };
const PRIORITY_COLOR = { high: '#d92d20', medium: '#b54708', low: '#667085', none: '#667085' };

export default function ResultRow({ result, requirement }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: '12px 16px', marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <strong>{STATUS_ICON[result.classification]} {requirement.skill_name}</strong>
          <span style={{ marginLeft: 8, fontSize: 13, color: '#667085' }}>
            {STATUS_LABEL[result.classification]} · {requirement.importance}
          </span>
        </div>
        {result.priority !== 'none' && (
          <span style={{ fontSize: 12, fontWeight: 600, color: PRIORITY_COLOR[result.priority] }}>
            {result.priority.toUpperCase()} PRIORITY
          </span>
        )}
      </div>

      <p style={{ margin: '8px 0 0', fontSize: 14, color: '#344054' }}>{result.explanation}</p>

      <button
        onClick={() => setShowDetails(!showDetails)}
        style={{ fontSize: 12, color: '#667085', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0' }}
      >
        {showDetails ? 'Hide' : 'Show'} technical details

      </button>

      {showDetails && (
        <div style={{ fontSize: 12, color: '#667085', marginTop: 4 }}>
          Similarity: {result.similarity_score ?? 'n/a'} · Method: {result.match_method} · Source: {result.explanation_source}
        </div>
      )}
    </div>
  );
}