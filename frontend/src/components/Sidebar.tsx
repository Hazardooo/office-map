// src/components/Sidebar.tsx
import { PrinterForm } from "./PrinterForm";
import { PrinterDetails } from "./PrinterDetails";
import { Printer } from "@/lib/api";

interface SidebarProps {
    loading: boolean;
    onMapUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
    clickCoords: { x: number; y: number } | null;
    newPrinter: { name: string; ip: string; vendor: "hp" | "kyocera" | "canon" };
    setNewPrinter: (data: any) => void;
    onCreatePrinter: (e: React.FormEvent) => void;
    setClickCoords: (coords: null) => void;
    selectedPrinter: Printer | null;
    onRefresh: (id: number) => void;
}

export function Sidebar({
                            loading,
                            onMapUpload,
                            clickCoords,
                            newPrinter,
                            setNewPrinter,
                            onCreatePrinter,
                            setClickCoords,
                            selectedPrinter,
                            onRefresh
                        }: SidebarProps) {
    return (
        <aside className="w-80 bg-zinc-950 p-6 flex flex-col gap-6 border-r border-zinc-800 overflow-y-auto">
            <div>
                <h1 className="text-xl font-bold tracking-tight mb-1">Мониторинг Принтеров</h1>
                <p className="text-xs text-zinc-400">Интерактивная карта офиса</p>
            </div>

            <div className="p-4 bg-zinc-900 rounded-lg border border-zinc-800">
                <label className="block text-sm font-medium mb-2 text-zinc-300">Обновить SVG-карту</label>
                <input
                    type="file"
                    accept=".svg"
                    onChange={onMapUpload}
                    className="w-full text-xs text-zinc-400 file:mr-4 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 cursor-pointer"
                />
                {loading && <p className="text-xs text-amber-400 mt-2">Загрузка файла на сервер...</p>}
            </div>

            {clickCoords && (
                <PrinterForm
                    clickCoords={clickCoords}
                    newPrinter={newPrinter}
                    onChange={setNewPrinter}
                    onSubmit={onCreatePrinter}
                    onCancel={() => setClickCoords(null)}
                />
            )}

            {selectedPrinter && (
                <PrinterDetails
                    printer={selectedPrinter}
                    onRefresh={onRefresh}
                />
            )}
        </aside>
    );
}