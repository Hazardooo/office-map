import {PrinterForm} from "./PrinterForm";
import {PrinterDetails} from "./PrinterDetails";
import {Printer} from "@/lib/api";

interface SidebarProps {
    loading: boolean;
    totalPrinters: number;
    mode: "view" | "add" | "move";
    onMapUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
    clickCoords: { x: number; y: number } | null;
    newPrinter: { name: string; ip: string; vendor: "hp" | "kyocera" | "canon" };
    setNewPrinter: (data: any) => void;
    onCreatePrinter: (e: React.FormEvent) => void;
    setClickCoords: (coords: null) => void;
    selectedPrinter: Printer | null;
    onRefresh: (id: string) => void;
    onDelete: (id: string) => void;
    onStartMove: () => void;
    onCancelMove: () => void;
    onRename: (id: string, newName: string) => void;
}

export function Sidebar({
                            loading,
                            totalPrinters,
                            mode,
                            onMapUpload,
                            clickCoords,
                            newPrinter,
                            setNewPrinter,
                            onCreatePrinter,
                            setClickCoords,
                            selectedPrinter,
                            onRefresh,
                            onDelete,
                            onStartMove,
                            onCancelMove,
                            onRename,
                        }: SidebarProps) {
    return (
        <aside
            className="w-[425px] flex-shrink-0 bg-zinc-950 p-6 flex flex-col gap-6 border-r border-zinc-800 overflow-y-auto">
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-xl font-bold tracking-tight mb-1">Мониторинг принтеров: {totalPrinters}</h1>
                </div>
            </div>

            {/* Индикатор режима */}
            {mode === "move" && (
                <div className="p-3 bg-amber-950/50 border border-amber-600/30 rounded-lg">
                    <p className="text-xs text-amber-400 font-medium">Режим перемещения</p>
                    <p className="text-[11px] text-amber-500/80 mt-1">
                        Кликните на карту, чтобы переместить «{selectedPrinter?.name || selectedPrinter?.ip}»
                    </p>
                    <button
                        onClick={onCancelMove}
                        className="mt-2 text-[11px] text-zinc-400 hover:text-zinc-200 underline"
                    >
                        Отмена
                    </button>
                </div>
            )}

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

            {clickCoords && mode === "add" && (
                <PrinterForm
                    clickCoords={clickCoords}
                    newPrinter={newPrinter}
                    onChange={setNewPrinter}
                    onSubmit={onCreatePrinter}
                    onCancel={() => {
                        setClickCoords(null);
                        onCancelMove();
                    }}
                />
            )}

            {selectedPrinter && mode !== "move" && (
                <PrinterDetails
                    printer={selectedPrinter}
                    onRefresh={onRefresh}
                    onDelete={onDelete}
                    onMove={onStartMove}
                    onRename={onRename}
                />
            )}
        </aside>
    );
}
