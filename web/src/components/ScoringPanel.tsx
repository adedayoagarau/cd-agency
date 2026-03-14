import { useStore } from "../store";

export function ScoringPanel() {
  const { scores } = useStore();

  if (!scores) {
    return (
      <aside className="scoring-panel">
        <div className="sidebar-label">SCORING</div>
        <div className="empty-state-sm">Type or score content to see results</div>
      </aside>
    );
  }

  const { readability, lint, a11y } = scores;
  const easeClass =
    readability.flesch_reading_ease >= 60 ? "good" :
    readability.flesch_reading_ease >= 30 ? "warn" : "bad";

  return (
    <aside className="scoring-panel">
      <div className="sidebar-label">SCORING</div>

      <div className="score-section">
        <div className="score-heading">Readability</div>
        <div className={`score-value score-${easeClass}`}>
          Flesch: {readability.flesch_reading_ease.toFixed(1)}
        </div>
        <div className="score-detail">Grade: {readability.grade_label}</div>
        <div className="score-detail">Words: {readability.word_count}</div>
        <div className="score-detail">Chars: {readability.character_count}</div>
      </div>

      <div className="score-section">
        <div className="score-heading">Lint</div>
        {lint.failed_count === 0 ? (
          <div className="score-value score-good">All checks passed</div>
        ) : (
          <>
            {lint.failed_count > 0 && (
              <div className="score-value score-warn">
                {lint.failed_count} issue{lint.failed_count > 1 ? "s" : ""}
              </div>
            )}
            {lint.issues
              .filter((i) => !i.passed)
              .slice(0, 3)
              .map((issue, idx) => (
                <div key={idx} className="score-detail">
                  {issue.rule}: {issue.message}
                </div>
              ))}
          </>
        )}
      </div>

      <div className="score-section">
        <div className="score-heading">Accessibility</div>
        {a11y.passed ? (
          <div className="score-value score-good">Pass</div>
        ) : (
          <>
            <div className="score-value score-bad">
              {a11y.issue_count} issue{a11y.issue_count > 1 ? "s" : ""}
            </div>
            {a11y.issues.slice(0, 3).map((issue, idx) => (
              <div key={idx} className="score-detail">{issue.rule}</div>
            ))}
          </>
        )}
      </div>
    </aside>
  );
}
