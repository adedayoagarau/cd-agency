import { Download } from "lucide-react";

interface Invoice {
  id: string;
  date: string;
  amount: string;
  status: "paid" | "pending";
}

const statusStyles: Record<Invoice["status"], string> = {
  paid: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
};

export function InvoiceTable({ invoices }: { invoices: Invoice[] }) {
  return (
    <div className="bg-surface-card rounded-xl shadow-soft overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-stone-100">
            <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wider">
              Date
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wider">
              Amount
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wider">
              Status
            </th>
            <th className="text-right px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wider">
              PDF
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-100">
          {invoices.map((inv) => (
            <tr key={inv.id} className="hover:bg-stone-50/50 transition-colors">
              <td className="px-4 py-3 text-stone-700">{inv.date}</td>
              <td className="px-4 py-3 text-stone-900 font-medium">
                {inv.amount}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${statusStyles[inv.status]}`}
                >
                  {inv.status}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button className="text-brand-600 text-xs hover:text-brand-700 transition-colors inline-flex items-center gap-1">
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
