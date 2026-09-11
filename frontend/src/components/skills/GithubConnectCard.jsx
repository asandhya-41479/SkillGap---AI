export default function GitHubConnectCard({ status, onConnect, onAnalyze, analyzing }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
      <div>
        {status?.connected ? (
          <>
            <p className="font-semibold text-green-700">✓ Connected as {status.github_username}</p>
            <p className="text-sm text-gray-500">
              {status.last_synced_at ? `Last analyzed: ${new Date(status.last_synced_at).toLocaleString()}` : 'Not analyzed yet'}
            </p>
          </>
        ) : (
          <p className="text-gray-600">Connect your GitHub account to detect demonstrated skills</p>
        )}
      </div>
      {status?.connected ? (
        <button onClick={onAnalyze} disabled={analyzing} className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-900 disabled:opacity-50">
          {analyzing ? 'Analyzing...' : 'Analyze Repositories'}
        </button>
      ) : (
        <button onClick={onConnect} className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
          Connect GitHub
        </button>
      )}
    </div>
  );
}