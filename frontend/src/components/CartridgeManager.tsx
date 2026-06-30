import {api, Cartridge} from "@/service/api";
import {useState} from "react";

interface CartridgeManagerProps {
    cartridges: Cartridge[];
    selectedCartridgeId: string | null;
    onSelectCartridge: (id: string | null) => void;
    onRefresh: () => void;
    setHoveredCartridgeId: (id: string | null) => void;
    isLinking: boolean;
    setIsLinking: (linking: boolean) => void;
    linkingPrinterIds: string[];
    setLinkingPrinterIds: (ids: string[]) => void;
}

export function CartridgeManager(props: CartridgeManagerProps) {
    const {
        cartridges, selectedCartridgeId, onSelectCartridge, onRefresh,
        setHoveredCartridgeId, isLinking, setIsLinking, linkingPrinterIds, setLinkingPrinterIds
    } = props;

    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [form, setForm] = useState({ name: "", color: "Black", quantity: 0, shop_link: "" });

    const openAddForm = () => {
        setForm({name: "", color: "Black", quantity: 0, shop_link: ""});
        setLinkingPrinterIds([]);
        setIsLinking(true);
        setEditingId(null);
        setIsFormOpen(true);
    };

    const openEditForm = (c: Cartridge, e: React.MouseEvent) => {
        e.stopPropagation();
        setForm({ name: c.name, color: c.color, quantity: c.quantity, shop_link: c.shop_link || "" });
        setLinkingPrinterIds(c.printer_ids || []);
        setIsLinking(true);
        setEditingId(c.id);
        setIsFormOpen(true);
    };

    const handleCancel = () => {
        setIsLinking(false);
        setIsFormOpen(false);
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const data = {...form, shop_link: form.shop_link || null, printer_ids: linkingPrinterIds};
            if (editingId) await api.updateCartridge(editingId, data);
            else await api.createCartridge(data);

            setIsLinking(false);
            setIsFormOpen(false);
            if (onRefresh) onRefresh();
        } catch (error: any) {
            console.error("Ошибка сохранения:", error);
            alert("Ошибка сохранения: " + (error.message || "проверьте консоль"));
        }
    };

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm("Удалить этот картридж?")) return;
        try {
            await api.deleteCartridge(id);
            if (selectedCartridgeId === id) onSelectCartridge(null);
            if (onRefresh) onRefresh();
        } catch (error: any) {
            console.error("Ошибка удаления:", error);
            alert("Ошибка удаления: " + (error.message || "проверьте консоль"));
        }
    };

    const handleUpdateQuantity = async (id: string, currentQty: number, delta: number, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.updateCartridge(id, {quantity: Math.max(0, currentQty + delta)});
            if (onRefresh) onRefresh();
        } catch (error: any) {
            console.error("Ошибка изменения остатков:", error);
        }
    };

    return (
        <div className="card-container border-t-4 border-t-brand mt-auto">
            <div className="flex justify-between items-center mb-4">
                <h4 className="font-bold text-text-main">База картриджей</h4>
                {!isLinking && (
                    <button onClick={openAddForm}
                            className="text-brand hover:text-brand-hover text-xs font-medium px-2 py-1 bg-surface-hover rounded transition-colors">
                        + Создать
                    </button>
                )}
            </div>

            <div className="space-y-2">
                {cartridges.length === 0 && !isFormOpen &&
                    <p className="text-xs text-text-dim text-center py-4">Склад пуст.</p>}

                {!isFormOpen && cartridges.map(c => {
                    const isSelected = selectedCartridgeId === c.id;
                    const linkedCount = c.printer_ids?.length || 0;

                    return (
                        <div
                            key={c.id}
                            onMouseEnter={() => setHoveredCartridgeId(c.id)}
                            onMouseLeave={() => setHoveredCartridgeId(null)}
                            onClick={() => onSelectCartridge(isSelected ? null : c.id)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected ? 'border-brand bg-brand-muted' : 'border-border bg-surface hover:bg-surface-hover'}`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full border border-surface-muted"
                                             style={{backgroundColor: c.color.toLowerCase() === 'black' ? '#52525b' : c.color.toLowerCase()}}/>
                                        <span className="text-sm font-bold text-text-main">{c.name}</span>
                                    </div>
                                    <p className="text-[10px] text-text-dim mt-0.5">Привязан к принтерам: {linkedCount}</p>
                                </div>
                                <div className="flex items-center bg-surface-muted rounded border border-border">
                                    <button onClick={(e) => handleUpdateQuantity(c.id, c.quantity, -1, e)}
                                            className="px-2.5 py-0.5 text-text-muted hover:text-white">-
                                    </button>
                                    <span className="px-2 text-xs font-mono text-brand w-6 text-center">{c.quantity}</span>
                                    <button onClick={(e) => handleUpdateQuantity(c.id, c.quantity, 1, e)}
                                            className="px-2.5 py-0.5 text-text-muted hover:text-white">+
                                    </button>
                                </div>
                            </div>

                            {isSelected && (
                                <div className="mt-3 pt-2 border-t border-brand-muted flex justify-between items-center">
                                    <button onClick={(e) => openEditForm(c, e)}
                                            className="text-xs text-brand hover:text-brand-hover">⚙️ Настроить связи
                                    </button>
                                    <div className="flex gap-3">
                                        {c.shop_link && <a href={c.shop_link} target="_blank" rel="noopener noreferrer"
                                                           className="text-xs text-blue-400 hover:text-blue-300">Заказать</a>}
                                        <button onClick={(e) => handleDelete(c.id, e)}
                                                className="text-xs text-status-offline hover:text-rose-400">Удалить
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {isFormOpen && (
                <div className="bg-surface border border-brand/50 rounded-xl p-4 shadow-lg mt-2">
                    <h3 className="font-bold text-sm mb-4 text-brand">{editingId ? "Настройка картриджа" : "Новый картридж"}</h3>
                    <form onSubmit={handleSave} className="space-y-4">
                        <div className="flex gap-2">
                            <input required type="text" placeholder="Артикул (TK-3190)"
                                   className="form-input text-sm w-full" value={form.name}
                                   onChange={e => setForm({...form, name: e.target.value})}/>
                            <input type="number" min="0" placeholder="Шт" className="form-input text-sm w-20"
                                   value={form.quantity}
                                   onChange={e => setForm({...form, quantity: parseInt(e.target.value) || 0})}/>
                        </div>
                        <input type="url" placeholder="Ссылка на магазин" className="form-input text-sm"
                               value={form.shop_link}
                               onChange={e => setForm({...form, shop_link: e.target.value})}/>

                        <div className="mt-4 p-3 bg-surface-muted border border-border-light rounded-lg text-center shadow-inner">
                            <p className="text-[11px] text-text-muted mb-2 leading-relaxed">
                                Кликайте по маркерам принтеров <strong className="text-text-main">на карте</strong> справа, чтобы связать их с этим картриджем.
                            </p>
                            <div className="inline-block bg-surface-hover border border-border rounded px-3 py-1">
                                <span className="text-xs text-text-dim">Выбрано связей: <strong className="text-brand text-sm ml-1">{linkingPrinterIds.length}</strong></span>
                            </div>
                        </div>

                        <div className="flex gap-2 pt-2">
                            <button type="submit" className="btn-primary text-sm py-1.5">Сохранить</button>
                            <button type="button" onClick={handleCancel}
                                    className="btn-secondary text-sm py-1.5">Отмена
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}