import React, { useEffect, useState } from 'react';
import { ShieldCheck, X, Clock, User, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

interface AuditLogModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuditLogModal: React.FC<AuditLogModalProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      api.getAuditLogs()
        .then(data => setLogs(Array.isArray(data) ? data : []))
        .catch(() => setLogs([]))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 font-sans text-sm">
      <div className="w-full max-w-3xl glass-panel bg-polar-950/95 border border-cyan-500/40 rounded-xl flex flex-col max-h-[80vh] shadow-2xl">
        {/* Modal Header */}
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-white text-base">
              Operational Decision & Audit Log (Human-in-the-Loop Traceability)
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-polar-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {loading ? (
            <div className="text-center py-8 text-slate-400 text-sm">Loading audit trail...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">No audit log entries recorded.</div>
          ) : (
            logs.map((log: any) => (
              <div
                key={log.entry_id}
                className="p-3.5 rounded-lg bg-polar-900 border border-slate-800 text-slate-300 space-y-2"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-cyan-300 flex items-center gap-1.5 font-sans text-sm">
                    <FileText className="w-4 h-4" /> {String(log.action_type || '').replace('AuditActionType.', '')}
                  </span>
                  <span className="text-slate-400 font-mono flex items-center gap-1 text-xs">
                    <Clock className="w-3.5 h-3.5" /> {new Date(log.timestamp).toLocaleString()}
                  </span>
                </div>

                <p className="text-slate-100 text-sm font-sans leading-relaxed">{log.rationale}</p>

                <div className="flex items-center justify-between text-xs text-slate-400 pt-1.5 border-t border-slate-800/80">
                  <span>Target: <strong className="text-slate-300 font-mono">{log.target_id}</strong></span>
                  <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                    <User className="w-3.5 h-3.5" /> Signed: {log.operator_id}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-sans">
          <span>All operator decisions, route overrides, and alerts are persistently archived.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-polar-800 hover:bg-polar-750 text-white font-medium text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
