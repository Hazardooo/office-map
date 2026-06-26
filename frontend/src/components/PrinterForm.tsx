// src/components/PrinterForm.tsx
interface PrinterFormProps {
    clickCoords: { x: number; y: number };
    newPrinter: { name: string; ip: string; vendor: "hp" | "kyocera" | "canon" };
    onChange: (data: unknown) => void;
    onSubmit: (e: React.FormEvent) => void;
    onCancel: () => void;
}

export function PrinterForm({ clickCoords, newPrinter, onChange, onSubmit, onCancel }: PrinterFormProps) {
    return (
        <div className="p-4 bg-zinc-900 rounded-lg border border-amber-500/30 text-sm">
            <h3 className="text-sm font-semibold text-amber-400 mb-3">Новое устройство</h3>
            <form onSubmit={onSubmit} className="flex flex-col gap-3">
                <div>
                    <label className="block text-xs text-zinc-400 mb-1">Позиция на плане</label>
                    <span className="text-xs font-mono text-zinc-500">X: {clickCoords.x}%, Y: {clickCoords.y}%</span>
                </div>
                <div>
                    <label className="block text-xs mb-1">Название / Комната</label>
                    <input
                        type="text"
                        required
                        value={newPrinter.name}
                        onChange={e => onChange({...newPrinter, name: e.target.value})}
                        className="form-input"
                        placeholder="Принтер Бухгалтерия"
                    />
                </div>
                <div>
                    <label className="block text-xs mb-1">IP-Адрес</label>
                    <input
                        type="text"
                        required
                        pattern="^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
                        value={newPrinter.ip}
                        onChange={e => onChange({...newPrinter, ip: e.target.value})}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-100 font-mono focus:outline-none focus:border-amber-500"
                        placeholder="192.168.1.15"
                    />
                </div>
                <div>
                    <label className="block text-xs mb-1">Производитель</label>
                    <select
                        value={newPrinter.vendor}
                        onChange={e => onChange({...newPrinter, vendor: e.target.value as any})}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-100 focus:outline-none focus:border-amber-500"
                    >
                        <option value="hp">HP</option>
                        <option value="kyocera">Kyocera</option>
                        <option value="canon">Canon</option>
                    </select>
                </div>
                <div className="flex gap-2 mt-2">
                    <button type="submit" className="btn-primary">Сохранить</button>
                    <button type="button" onClick={onCancel} className="btn-secondary">Отмена</button>
                </div>
            </form>
        </div>
    );
}