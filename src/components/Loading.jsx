export default function Loading({ error }) {
  if (error) {
    return (
      <div className="px-6 py-24 text-center text-sm text-muted-3">
        Couldn't load the module mappings. Check your connection and{' '}
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="font-semibold text-accent hover:text-accent-hover"
        >
          try again
        </button>
        .
      </div>
    );
  }
  return <div className="px-6 py-24 text-center text-sm text-muted-3">Loading module mappings…</div>;
}
