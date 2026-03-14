export function HelpModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
        <h2>CD Agency Studio</h2>
        <div className="help-grid">
          <div>
            <h3>Tabs</h3>
            <ul>
              <li><strong>Chat</strong> — Multi-turn conversation with agents</li>
              <li><strong>Form</strong> — Structured content editor with output</li>
              <li><strong>Workflow</strong> — Run multi-agent pipelines</li>
              <li><strong>Batch</strong> — Process multiple inputs at once</li>
              <li><strong>History</strong> — Browse version history with diffs</li>
              <li><strong>Scrape</strong> — Fetch and analyze web page content</li>
            </ul>
          </div>
          <div>
            <h3>Getting Started</h3>
            <ol>
              <li>Set your Anthropic API key (top right)</li>
              <li>Select an agent from the sidebar</li>
              <li>Start chatting or use form mode</li>
              <li>Scores update live in the right panel</li>
            </ol>
            <h3>File Access</h3>
            <p>Use the Open/Save buttons in Form mode to read and write local files directly.</p>
          </div>
        </div>
        <div className="modal-actions">
          <button className="btn btn-primary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
