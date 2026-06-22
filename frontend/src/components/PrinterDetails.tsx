// src/components/PrinterDetails.tsx
import { Printer } from "@/lib/api";

interface PrinterDetailsProps {
    printer: Printer;
    onRefresh: (id: number) => void;
}

export function PrinterDetails({ printer, onRefresh }: PrinterDetailsProps) {
    return (
        <div className="card-container">
            <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-zinc-100">{printer.name || "Без имени"}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${printer.status === 'online' ? 'bg-green-950 text-green-400 border border-green-800' : 'bg-red-950 text-red-400 border border-red-800'}`}>
                    {printer.status}
                </span>
            </div>

            <div className="space-y-1 text-xs text-zinc-300 font-mono mb-4">
                <p><span className="text-zinc-500">IP:</span> {printer.ip}</p>
                <p><span className="text-zinc-500">Бренд:</span> {printer.vendor.toUpperCase()}</p>
                {printer.model && <p><span className="text-zinc-500">Модель:</span> {printer.model}</p>}
                {printer.serial_number && <p><span className="text-zinc-500">S/N:</span> {printer.serial_number}</p>}
            </div>

            <div className="space-y-2 border-t border-zinc-800 pt-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1">Расходные материалы</h4>
                <div>
                    <div className="flex justify-between text-xs mb-1"><span>Черный (K)</span><span>{printer.toner_black}%</span></div>
                    <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                        <div className="bg-zinc-400 h-full" style={{ width: `${printer.toner_black}%` }}></div>
                    </div>
                </div>

                {printer.toner_cyan !== null && printer.toner_cyan !== undefined && (
                    <div className="grid grid-cols-3 gap-2 pt-1">
                        <div>
                            <div className="text-[10px] text-cyan-400">C: {printer.toner_cyan}%</div>
                            <div className="w-full bg-zinc-800 h-1.5 rounded-full"><div className="bg-cyan-400 h-full" style={{ width: `${printer.toner_cyan}%` }}></div></div>
                        </div>
                        <div>
                            <div className="text-[10px] text-fuchsia-400">M: {printer.toner_magenta}%</div>
                            <div className="w-full bg-zinc-800 h-1.5 rounded-full"><div className="bg-fuchsia-400 h-full" style={{ width: `${printer.toner_magenta}%` }}></div></div>
                        </div>
                        <div>
                            <div className="text-[10px] text-yellow-400">Y: {printer.toner_yellow}%</div>
                            <div className="w-full bg-zinc-800 h-1.5 rounded-full"><div className="bg-yellow-400 h-full" style={{ width: `${printer.toner_yellow}%` }}></div></div>
                        </div>
                    </div>
                )}
            </div>

            <button onClick={() => onRefresh(printer.id)} className="btn-secondary w-full mt-4 text-xs">
                Запросить статус по сети
            </button>
        </div>
    );
}