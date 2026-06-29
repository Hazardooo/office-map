import {api, Cartridge} from "@/service/api";
import {useState} from "react";

interface CartridgeManagerProps {
    cartridges: Cartridge[];
    selectedCartridgeId: string | null;
    onSelectCartridge: (id: string | null) => void;
    onRefresh: () => void;

    // Внешний стейт для связывания
    setHoveredCartridgeId: (id: string | null) => void;
    isLinking: boolean;
    setIsLinking: (linking: boolean) => void;
    linkingPrinterIds: string[];
    setLinkingPrinterIds: (ids: string[]) => void;
}

export function CartridgeManager({
                                     cartridges,
                                     selectedCartridgeId,
                                     onSelectCartridge,
                                     onRefresh,
                                     setHoveredCartridgeId,
                                     isLinking,
                                     setIsLinking,
                                     linkingPrinterIds,
                                     setLinkingPrinterIds
                                 }: CartridgeManagerProps) {
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [form, setForm] = useState({
        name: "",
        color: "Black",
        quantity: 0,
        shop_link: ""
    });

    const openAddForm = () => {
        setForm({name: "", color: "Black", quantity: 0, shop_link: ""});
        setLinkingPrinterIds([]);
        setIsLinking(true);
        setEditingId(null);
        setIsFormOpen(true);
    };

    const openEditForm = (c: Cartridge, e: React.MouseEvent) => {
        e.stopPropagation();
        setForm({
            name: c.name,
            color: c.color,
            quantity: c.quantity,
            shop_link: c.shop_link || ""
        });
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
            // При сохранении берем массив связей из внешнего стейта linkingPrinterIds
            const data = {...form, shop_link: form.shop_link || null, printer_ids: linkingPrinterIds};
            if (editingId) await api.updateCartridge(editingId, data);
            else await api.createCartridge(data);

            setIsLinking(false);
            setIsFormOpen(false);
            onRefresh();
        } catch (error) {
            alert("Ошибка сохранения картриджа");
        }
    };

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm("Удалить этот картридж?")) return;
        try {
            await api.deleteCartridge(id);
            if (selectedCartridgeId === id) onSelectCartridge(null);
            onRefresh();
        } catch (error) {
            console.error("Ошибка удаления");
        }
    };

    const handleUpdateQuantity = async (id: string, currentQty: number, delta: number, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.updateCartridge(id, {quantity: Math.max(0, currentQty + delta)});
            onRefresh();
        } catch (error) {
            console.error("Ошибка изменения остатков");
        }
    };

    return (
        <div className="card-container border-t-4 border-t-amber-600">
            <div className="flex justify-between items-center mb-4">
                <h4 className="font-bold text-zinc-100">База картриджей</h4>
                {!isLinking && (
                    <button onClick={openAddForm}
                            className="text-amber-500 hover:text-amber-400 text-xs font-medium px-2 py-1 bg-zinc-800 rounded transition-colors">
                        + Создать
                    </button>
                )}
            </div>

            <div className="space-y-2">
                {cartridges.length === 0 && !isFormOpen &&
                    <p className="text-xs text-zinc-500 text-center py-4">Склад пуст.</p>}

                {!isFormOpen && cartridges.map(c => {
                    const isSelected = selectedCartridgeId === c.id;
                    const linkedCount = c.printer_ids?.length || 0;

                    return (
                        <div
                            key={c.id}
                            onMouseEnter={() => setHoveredCartridgeId(c.id)}
                            onMouseLeave={() => setHoveredCartridgeId(null)}
                            onClick={() => onSelectCartridge(isSelected ? null : c.id)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected ? 'border-amber-500 bg-amber-500/10' : 'border-zinc-700 bg-zinc-800/50 hover:bg-zinc-800'}`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full border border-zinc-900"
                                             style={{backgroundColor: c.color.toLowerCase() === 'black' ? '#52525b' : c.color.toLowerCase()}}/>
                                        <span className="text-sm font-bold text-zinc-100">{c.name}</span>
                                    </div>
                                    <p className="text-[10px] text-zinc-500 mt-0.5">Привязан к принтерам: {linkedCount}</p>
                                </div>
                                <div className="flex items-center bg-zinc-900 rounded border border-zinc-700">
                                    <button onClick={(e) => handleUpdateQuantity(c.id, c.quantity, -1, e)}
                                            className="px-2.5 py-0.5 text-zinc-400 hover:text-white">-
                                    </button>
                                    <span className="px-2 text-xs font-mono text-amber-400 w-6 text-center">{c.quantity}</span>
                                    <button onClick={(e) => handleUpdateQuantity(c.id, c.quantity, 1, e)}
                                            className="px-2.5 py-0.5 text-zinc-400 hover:text-white">+
                                    </button>
                                </div>
                            </div>

                            {isSelected && (
                                <div className="mt-3 pt-2 border-t border-amber-500/20 flex justify-between items-center">
                                    <button onClick={(e) => openEditForm(c, e)}
                                            className="text-xs text-amber-500 hover:text-amber-400">⚙️ Настроить связи
                                    </button>
                                    <div className="flex gap-3">
                                        {c.shop_link && <a href={c.shop_link} target="_blank" rel="noopener noreferrer"
                                                           className="text-xs text-blue-400 hover:text-blue-300">Заказать</a>}
                                        <button onClick={(e) => handleDelete(c.id, e)}
                                                className="text-xs text-rose-500 hover:text-rose-400">Удалить
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {isFormOpen && (
                <div className="bg-zinc-900 border border-amber-500/50 rounded-xl p-4 shadow-lg mt-2">
                    <h3 className="font-bold text-sm mb-4 text-amber-500">{editingId ? "Настройка картриджа" : "Новый картридж"}</h3>
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

                        {/* Интерактивная зона-подсказка вместо чекбоксов */}
                        <div className="mt-4 p-3 bg-zinc-950 border border-zinc-800 rounded-lg text-center shadow-inner">
                            <p className="text-[11px] text-zinc-400 mb-2 leading-relaxed">
                                Кликайте по маркерам принтеров <strong className="text-zinc-200">на карте</strong> справа, чтобы связать их с этим картриджем.
                            </p>
                            <div className="inline-block bg-zinc-800 border border-zinc-700 rounded px-3 py-1">
                                <span className="text-xs text-zinc-300">Выбрано связей: <strong className="text-amber-400 text-sm ml-1">{linkingPrinterIds.length}</strong></span>
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