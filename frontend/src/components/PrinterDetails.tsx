import {Printer} from "@/lib/api";
import {useState} from "react";

interface PrinterDetailsProps {
    printer: Printer;
    onRefresh: (id: string) => void;
    onDelete: (id: string) => void;
    onMove: () => void;
    onRename: (id: string, newName: string) => void;
}

export function PrinterDetails({printer, onRefresh, onDelete, onMove, onRename}: PrinterDetailsProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState(printer.name || "");

    const handleSave = () => {
        onRename(printer.id, editName.trim());
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditName(printer.name || "");
        setIsEditing(false);
    };

    return (
        <div className="card-container">
            <div className="flex justify-between items-start mb-1">
                {isEditing ? (
                    <div className="flex-1 mr-2">
                        <input
                            type="text"
                            value={editName}
                            onChange={e => setEditName(e.target.value)}
                            className="form-input text-sm font-bold"
                            placeholder="Название принтера"
                            autoFocus
                            onKeyDown={e => {
                                if (e.key === 'Enter') handleSave();
                                if (e.key === 'Escape') handleCancel();
                            }}
                        />
                        <div className="flex gap-2 mt-2">
                            <button onClick={handleSave} className="btn-primary text-xs py-1">Сохранить</button>
                            <button onClick={handleCancel} className="btn-secondary text-xs py-1">Отмена</button>
                        </div>
                    </div>
                ) : (
                    <h3
                        className="font-bold text-zinc-100 cursor-pointer hover:text-amber-400 transition-colors"
                        onClick={() => setIsEditing(true)}
                        title="Кликните для редактирования"
                    >
                        {printer.name || "Без имени"}
                    </h3>
                )}
                <span
                    className={`... ${printer.is_online ? 'bg-green-950 text-green-400' : 'bg-red-950 text-red-400'}`}>
                        {printer.is_online ? 'online' : 'offline'}
                </span>
            </div>

            <div className="space-y-1 text-xs text-zinc-300 font-mono mb-4">
                <p><span className="text-zinc-500">IP:</span> {printer.ip}</p>
                <p><span className="text-zinc-500">Бренд:</span> {printer.vendor.toUpperCase()}</p>
                {printer.model && <p><span className="text-zinc-500">Модель:</span> {printer.model}</p>}
                {printer.serial_number && <p><span className="text-zinc-500">S/N:</span> {printer.serial_number}</p>}
                <p><span className="text-zinc-500">Позиция:</span> X:{printer.x}% Y:{printer.y}%</p>
            </div>

            <div className="space-y-2 border-t border-zinc-800 pt-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1">Расходные
                    материалы</h4>
                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span>Черный (K)</span><span>{printer.toner_black}%</span></div>
                    <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                        <div className="bg-zinc-400 h-full" style={{width: `${printer.toner_black}%`}}></div>
                    </div>
                </div>

                {printer.toner_cyan !== null && printer.toner_cyan !== undefined && (
                    <div className="grid grid-cols-3 gap-2 pt-1">
                        <div>
                            <div className="text-[10px] text-cyan-400">C: {printer.toner_cyan}%</div>
                            <div className="w-full bg-zinc-800 h-1.5 rounded-full">
                                <div className="bg-cyan-400 h-full" style={{width: `${printer.toner_cyan}%`}}></div>
                            </div>
                        </div>
                        <div>
                            <div className="text-[10px] text-fuchsia-400">M: {printer.toner_magenta}%</div>
                            <div className="w-full bg-zinc-800 h-1.5 rounded-full">
                                <div className="bg-fuchsia-400 h-full"
                                     style={{width: `${printer.toner_magenta}%`}}></div>
                            </div>
                        </div>
                        <div>
                            <div className="text-[10px] text-yellow-400">Y: {printer.toner_yellow}%</div>
                            <div className="w-full bg-zinc-800 h-1.5 rounded-full">
                                <div className="bg-yellow-400 h-full" style={{width: `${printer.toner_yellow}%`}}></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 gap-2 mt-4">
                <button
                    onClick={() => onRefresh(printer.id)}
                    className="btn-primary text-xs"
                >
                    Обновить
                </button>
                <button
                    onClick={onMove}
                    className="btn-secondary text-xs"
                >
                    Редактировать
                </button>
                <button
                    onClick={() => onDelete(printer.id)}
                    className="btn-danger text-xs"
                >
                    Удалить
                </button>
            </div>
        </div>
    );
}
