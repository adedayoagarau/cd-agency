import { useState } from "react";
import { useStore } from "../store";

export function ApiKeyModal() {
  const { apiKey, setApiKey } = useStore();
  const [value, setValue] = useState(apiKey);
  const [open, setOpen] = useState(!apiKey);

  if (!open) return null;

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Anthropic API Key</h2>
        <p>Enter your Anthropic API key to run agents. Your key is stored only in this browser and sent directly to the Anthropic API.</p>
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="sk-ant-..."
          className="input-full"
          autoFocus
        />
        <div className="modal-actions">
          {apiKey && (
            <button className="btn" onClick={() => setOpen(false)}>Cancel</button>
          )}
          <button
            className="btn btn-primary"
            onClick={() => { setApiKey(value); setOpen(false); }}
            disabled={!value.trim()}
          >
            Save Key
          </button>
        </div>
      </div>
    </div>
  );
}

export function ApiKeyButton() {
  const { apiKey, setApiKey } = useStore();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(apiKey);

  return (
    <>
      <button
        className={`btn btn-sm ${apiKey ? "btn-success" : "btn-warn"}`}
        onClick={() => { setValue(apiKey); setOpen(true); }}
        title={apiKey ? "API key set" : "No API key"}
      >
        {apiKey ? "Key Set" : "Set API Key"}
      </button>
      {open && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Anthropic API Key</h2>
            <input
              type="password"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="sk-ant-..."
              className="input-full"
              autoFocus
            />
            <div className="modal-actions">
              <button className="btn" onClick={() => setOpen(false)}>Cancel</button>
              {apiKey && (
                <button className="btn btn-danger" onClick={() => { setApiKey(""); setOpen(false); }}>
                  Clear Key
                </button>
              )}
              <button
                className="btn btn-primary"
                onClick={() => { setApiKey(value); setOpen(false); }}
                disabled={!value.trim()}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
