// src/components/CartridgeManager.tsx
import {api, Cartridge, Printer} from "@/service/api";
import {useEffect, useState} from "react";

interface CartridgeManagerProps {
    printer: Printer;
}

export function CartridgeManager({ printer }: CartridgeManagerProps) {
    const [cartridges, setCartridges] = useState<Cartridge[]>([]);
    const [isAdding, setIsAdding] = useState(false);
    const [newCartridge, setNewCartridge] = useState({
        name: "",
        color: "Black",
        quantity: 0,
        shop_link: ""
    });

    useEffect(() => {
        if (printer.model && printer.model !== "Unknown") {
            api.getCartridgesByPrinter(printer.model)
                .then(setCartridges)
                .catch(console.error);
        } else {
            setCartridges([]);
        }
    }, [printer.model]);

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!printer.model) return;
        try {
            const added = await api.createCartridge({
                ...newCartridge,
                printer_model: printer.model,
                shop_link: newCartridge.shop_link || null
            });
            setCartridges(prev => [...prev, added]);
            setIsAdding(false);
            setNewCartridge({ name: "", color: "Black", quantity: 0, shop_link: "" });
        } catch (error) {
            alert("Не удалось добавить картридж");
        }
    };

    const handleUpdateQuantity = async (id: string, currentQty: number, delta: number) => {
        const newQty = Math.max(0, currentQty + delta);
        try {
            const updated = await api.updateCartridge(id, { quantity: newQty });
            setCartridges(prev => prev.map(c => c.id === id ? updated : c));
        } catch (error) {
            console.error("Ошибка обновления остатков");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Удалить этот картридж из базы?")) return;
        try {
            await api.deleteCartridge(id);
            setCartridges(prev => prev.filter(c => c.id !== id));
        } catch (error) {
            console.error("Ошибка удаления");
        }
    };

    return (
        <div className="card-container">
            <div className="flex justify-between items-center mb-4">
                <h4 className="font-bold text-zinc-100">Склад картриджей</h4>
                {printer.model && printer.model !== "Unknown" && (
                    <button
                        onClick={() => setIsAdding(!isAdding)}
                        className="text-amber-500 hover:text-amber-400 text-xs font-medium bg-amber-500/10 px-2 py-1 rounded"
                    >
                        {isAdding ? "Отмена" : "+ Добавить"}
                    </button>
                )}
            </div>

            {!printer.model || printer.model === "Unknown" ? (
                <div className="text-center p-4 border border-dashed border-zinc-700 rounded bg-zinc-800/30">
                    <p className="text-xs text-zinc-400">Модель принтера не определена.</p>
                    <p className="text-xs text-zinc-500 mt-1">Опросите принтер, чтобы привязать картриджи.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {cartridges.length === 0 && !isAdding && (
                        <p className="text-xs text-zinc-500 text-center py-2">Склад пуст. Добавьте первый картридж.</p>
                    )}

                    {cartridges.map(cartridge => (
                        <div key={cartridge.id} className="bg-zinc-800 p-3 rounded-lg border border-zinc-700">
                            <div className="flex justify-between items-start mb-2">
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-3 h-3 rounded-full border border-zinc-900"
                                        style={{ backgroundColor: cartridge.color.toLowerCase() === 'black' ? '#52525b' : cartridge.color.toLowerCase() }}
                                        title={cartridge.color}
                                    />
                                    <span className="text-sm font-bold text-zinc-100">{cartridge.name}</span>
                                </div>
                                <div className="flex items-center bg-zinc-900 rounded border border-zinc-700">
                                    <button onClick={() => handleUpdateQuantity(cartridge.id, cartridge.quantity, -1)} className="px-2.5 py-1 text-zinc-400 hover:text-white transition-colors">-</button>
                                    <span className="px-2 text-sm font-mono text-amber-400 w-8 text-center">{cartridge.quantity}</span>
                                    <button onClick={() => handleUpdateQuantity(cartridge.id, cartridge.quantity, 1)} className="px-2.5 py-1 text-zinc-400 hover:text-white transition-colors">+</button>
                                </div>
                            </div>
                            <div className="flex justify-between items-center mt-3 pt-2 border-t border-zinc-700/50">
                                {cartridge.shop_link ? (
                                    <a href={cartridge.shop_link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                                        🔗 Заказать онлайн
                                    </a>
                                ) : <span className="text-xs text-zinc-600">Ссылка не указана</span>}
                                <button onClick={() => handleDelete(cartridge.id)} className="text-xs text-rose-500 hover:text-rose-400 transition-colors">Удалить</button>
                            </div>
                        </div>
                    ))}

                    {isAdding && (
                        <form onSubmit={handleAdd} className="bg-zinc-950 p-3 rounded-lg border border-amber-500/30 flex flex-col gap-3 mt-4 shadow-inner">
                            <div>
                                <label className="block text-[10px] uppercase text-zinc-500 mb-1">Артикул</label>
                                <input required type="text" placeholder="Напр. TK-3190" className="form-input text-sm" value={newCartridge.name} onChange={e => setNewCartridge({...newCartridge, name: e.target.value})} />
                            </div>
                            <div className="flex gap-2">
                                <div className="w-1/2">
                                    <label className="block text-[10px] uppercase text-zinc-500 mb-1">Цвет</label>
                                    <select className="form-input text-sm" value={newCartridge.color} onChange={e => setNewCartridge({...newCartridge, color: e.target.value})}>
                                        <option value="Black">Черный</option>
                                        <option value="Cyan">Голубой</option>
                                        <option value="Magenta">Пурпурный</option>
                                        <option value="Yellow">Желтый</option>
                                    </select>
                                </div>
                                <div className="w-1/2">
                                    <label className="block text-[10px] uppercase text-zinc-500 mb-1">Остаток</label>
                                    <input type="number" min="0" className="form-input text-sm" value={newCartridge.quantity} onChange={e => setNewCartridge({...newCartridge, quantity: parseInt(e.target.value) || 0})} />
                                </div>
                            </div>
                            <div>
                                <label className="block text-[10px] uppercase text-zinc-500 mb-1">Ссылка на закупку (необязательно)</label>
                                <input type="url" placeholder="https://..." className="form-input text-sm" value={newCartridge.shop_link} onChange={e => setNewCartridge({...newCartridge, shop_link: e.target.value})} />
                            </div>
                            <button type="submit" className="btn-primary mt-2">Сохранить картридж</button>
                        </form>
                    )}
                </div>
            )}
        </div>
    );
}