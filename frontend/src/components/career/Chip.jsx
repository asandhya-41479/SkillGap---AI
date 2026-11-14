// Small coloured label. Lives in a .jsx file because Vite only compiles JSX in .jsx files.
export function Chip({ spec, children }) {
  return (
    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded ${spec?.cls || 'bg-gray-100 text-gray-700'}`}>
      {children ?? spec?.text}
    </span>
  );
}
