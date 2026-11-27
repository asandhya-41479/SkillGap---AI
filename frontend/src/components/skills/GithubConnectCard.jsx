// GitHub card: connect, re-analyse, and the languages found in your repositories.
const GH = 'M12 2C6.5 2 2 6.6 2 12.2c0 4.5 2.9 8.3 6.8 9.6.5.1.7-.2.7-.5v-1.8c-2.8.6-3.4-1.4-3.4-1.4-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.6 2.4 1.1 2.9.8.1-.7.4-1.1.6-1.4-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.5-1.3.1-2.7 0 0 .8-.3 2.8 1a9.4 9.4 0 015 0c1.9-1.3 2.8-1 2.8-1 .6 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9v2.8c0 .3.2.6.7.5A10.1 10.1 0 0022 12.2C22 6.6 17.5 2 12 2z';

export default function GitHubConnectCard({ status, onConnect, onAnalyze, analyzing, languages = [] }) {
  const connected = !!status?.connected;
  return (
    <section className="card flex flex-col gap-4 bg-navy text-white">
      <div className="flex items-start gap-3">
        <span className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-white text-ink">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d={GH} /></svg>
        </span>
        <div className="min-w-0">
          <h2 className="m-0 font-display text-lg font-bold">GitHub evidence</h2>
          {connected ? (
            <p className="m-0 mt-0.5 text-sm text-blue-100">
              Connected as <strong className="text-white">{status.github_username}</strong>
              <span className="ml-2 rounded-full bg-green-500/20 px-2 py-0.5 text-xs font-bold text-green-300">Connected</span>
            </p>
          ) : (
            <p className="m-0 mt-0.5 text-sm text-blue-100">Connect GitHub so your repositories can prove the skills you list.</p>
          )}
        </div>
      </div>

      {connected && (
        <>
          <p className="m-0 text-sm text-blue-100">
            {status.last_synced_at ? `Last analysed ${new Date(status.last_synced_at).toLocaleString()}` : 'Not analysed yet. Run an analysis to detect your languages.'}
          </p>
          {languages.length > 0 && (
            <div>
              <p className="eyebrow m-0 mb-2 text-blue-300">Languages found</p>
              <ul className="m-0 flex list-none flex-wrap gap-2 p-0">
                {languages.map((l) => <li key={l} className="rounded-full bg-white/10 px-3 py-1 text-sm font-semibold">{l}</li>)}
              </ul>
            </div>
          )}
        </>
      )}

      <div className="flex flex-wrap gap-2">
        {connected ? (
          <>
            <button type="button" onClick={onAnalyze} disabled={analyzing} className="btn-primary bg-white text-ink hover:bg-blue-50">
              {analyzing ? 'Analysing repositories…' : 'Analyse repositories'}
            </button>
            <button type="button" onClick={onConnect} className="btn-secondary border-white/30 bg-transparent text-white hover:bg-white/10">
              Reconnect GitHub
            </button>
          </>
        ) : (
          <button type="button" onClick={onConnect} className="btn-primary bg-white text-ink hover:bg-blue-50">Connect GitHub</button>
        )}
      </div>
    </section>
  );
}
