import { useState } from 'react';

function CopyButton({ text, label = 'Copy' }) {
  const [copied, setCopied] = useState(false);
  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard not available */
    }
  }
  return (
    <button onClick={handleCopy} className="btn-ghost" title="Copy to clipboard">
      {copied ? (
        <span className="text-emerald-400">✓ Copied!</span>
      ) : (
        <>{label}</>
      )}
    </button>
  );
}

export { CopyButton };
export default CopyButton;
