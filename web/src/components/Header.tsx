import { useState } from "react";
import { useStore } from "../store";
import { ApiKeyButton } from "./ApiKeyModal";
import { HelpModal } from "./HelpModal";
import { ExportModal } from "./ExportModal";

export function Header() {
  const [helpOpen, setHelpOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  return (
    <header className="header">
      <div className="header-title">CD Agency Studio</div>
      <div className="header-actions">
        <button className="btn btn-sm" onClick={() => setExportOpen(true)}>Export</button>
        <ApiKeyButton />
        <button className="btn btn-sm" onClick={() => setHelpOpen(true)}>Help</button>
      </div>
      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}
      {exportOpen && <ExportModal onClose={() => setExportOpen(false)} />}
    </header>
  );
}
