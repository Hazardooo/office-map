// src/app/page.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { api, Printer, BASE_URL } from "@/lib/api";

export default function OfficeMapPage() {
    const [printers, setPrinters] = useState<Printer[]>([]);
    const [mapUrl, setMapUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Состояния для добавления принтера
    const [clickCoords, setClickCoords] = useState<{ x: number; y: number } | null>(null);
    const [newPrinter, setNewPrinter] = useState({ name: "", ip: "", vendor: "hp" as "hp" | "kyocera" | "canon" });

    // Состояние выбранного принтера для просмотра деталей
    const [selectedPrinter, setSelectedPrinter] = useState<Printer | null>(null);

    const mapContainerRef = useRef<HTMLDivElement>(null);

    // Инициализация данных при загрузке страницы
    useEffect(() => {
        loadPrinters();
        loadCurrentMap();
    }, []);

    const loadPrinters = async () => {
        try {
            const data = await api.getPrinters();
            setPrinters(data);
        } catch (err) {
            console.error("Ошибка загрузки списка принтеров:", err);
        }
    };

    const loadCurrentMap = async () => {
        try {
            const data = await api.getCurrentMap();
            // Формируем полный URL: http://localhost:8000/maps/file/filename.svg
            setMapUrl(`${BASE_URL}${data.url}`);
        } catch (err) {
            console.log("Карта на бэкенде пока не установлена.");
            setMapUrl(null);
        }
    };

    // Загрузка файла карты через инпут
    const handleMapUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.[0]) return;
        setLoading(true);
        try {
            const response = await api.uploadMap(e.target.files[0]);
            setMapUrl(`${BASE_URL}${response.url}`);
            setClickCoords(null);
            alert("Карта успешно загружена и отображена!");
        } catch (err) {
            alert("Не удалось загрузить файл. Убедитесь, что это валидный .svg");
        } finally {
            setLoading(false);
        }
    };

    // Клик по карте для установки координат нового принтера
    const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!mapContainerRef.current) return;

        // Пропускаем клик, если нажали на маркер уже существующего принтера
        if ((e.target as HTMLElement).closest(".printer-marker")) return;

        const rect = mapContainerRef.current.getBoundingClientRect();
        // Вычисляем координаты в процентах (0-100%) относительно размеров контейнера
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        setClickCoords({ x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100 });
        setSelectedPrinter(null); // Закрываем карточку просмотра при создании нового
    };

    // Сабмит формы добавления принтера
    const handleCreatePrinter = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!clickCoords) return;

        try {
            await api.createPrinter({
                ...newPrinter,
                x: clickCoords.x,
                y: clickCoords.y
            });
            setClickCoords(null);
            setNewPrinter({ name: "", ip: "", vendor: "hp" });
            loadPrinters();
        } catch (err) {
            alert("Не удалось добавить принтер. Проверьте правильность IP адреса.");
        }
    };

    // Опрос принтера в реальном времени
    const handleRefresh = async (id: number) => {
        try {
            const updated = await api.refreshPrinter(id);
            setSelectedPrinter(updated);
            loadPrinters();
        } catch (err) {
            alert("Ошибка опроса принтера по SNMP/сеть.");
        }
    };

    return (
        <div className="flex h-screen bg-zinc-900 text-zinc-100 font-sans">
            {/* Левый сайдбар управления */}
            <aside className="w-80 bg-zinc-950 p-6 flex flex-col gap-6 border-r border-zinc-800 overflow-y-auto">
                <div>
                    <h1 className="text-xl font-bold tracking-tight mb-1">Мониторинг Принтеров</h1>
                    <p className="text-xs text-zinc-400">Интерактивная карта офиса</p>
                </div>

                {/* Секция обновления файла подложки */}
                <div className="p-4 bg-zinc-900 rounded-lg border border-zinc-800">
                    <label className="block text-sm font-medium mb-2 text-zinc-300">Обновить SVG-карту</label>
                    <input
                        type="file"
                        accept=".svg"
                        onChange={handleMapUpload}
                        className="w-full text-xs text-zinc-400 file:mr-4 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 cursor-pointer"
                    />
                    {loading && <p className="text-xs text-amber-400 mt-2">Загрузка файла на сервер...</p>}
                </div>

                {/* Форма создания принтера */}
                {clickCoords && (
                    <div className="p-4 bg-zinc-900 rounded-lg border border-amber-500/30">
                        <h3 className="text-sm font-semibold text-amber-400 mb-3">Новое устройство</h3>
                        <form onSubmit={handleCreatePrinter} className="flex flex-col gap-3 text-sm">
                            <div>
                                <label className="block text-xs text-zinc-400 mb-1">Позиция на плане</label>
                                <span className="text-xs font-mono text-zinc-500">X: {clickCoords.x}%, Y: {clickCoords.y}%</span>
                            </div>
                            <div>
                                <label className="block text-xs mb-1">Название / Комната</label>
                                <input type="text" required value={newPrinter.name} onChange={e => setNewPrinter({...newPrinter, name: e.target.value})} className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-100 focus:outline-none focus:border-amber-500" placeholder="Принтер Бухгалтерия" />
                            </div>
                            <div>
                                <label className="block text-xs mb-1">IP-Адрес</label>
                                <input type="text" required pattern="^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$" value={newPrinter.ip} onChange={e => setNewPrinter({...newPrinter, ip: e.target.value})} className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-100 font-mono focus:outline-none focus:border-amber-500" placeholder="192.168.1.15" />
                            </div>
                            <div>
                                <label className="block text-xs mb-1">Производитель</label>
                                <select value={newPrinter.vendor} onChange={e => setNewPrinter({...newPrinter, vendor: e.target.value as any})} className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-100 focus:outline-none focus:border-amber-500">
                                    <option value="hp">HP</option>
                                    <option value="kyocera">Kyocera</option>
                                    <option value="canon">Canon</option>
                                </select>
                            </div>
                            <div className="flex gap-2 mt-2">
                                <button type="submit" className="flex-1 bg-amber-600 hover:bg-amber-500 text-white rounded py-1.5 font-medium transition-colors">Сохранить</button>
                                <button type="button" onClick={() => setClickCoords(null)} className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded px-3 py-1.5 transition-colors">Отмена</button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Карточка детальной информации о принтере */}
                {selectedPrinter && (
                    <div className="p-4 bg-zinc-900 rounded-lg border border-zinc-800 text-sm">
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="font-bold text-zinc-100">{selectedPrinter.name || "Без имени"}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${selectedPrinter.status === 'online' ? 'bg-green-950 text-green-400 border border-green-800' : 'bg-red-950 text-red-400 border border-red-800'}`}>
                {selectedPrinter.status}
              </span>
                        </div>

                        <div className="space-y-1 text-xs text-zinc-300 font-mono mb-4">
                            <p><span className="text-zinc-500">IP:</span> {selectedPrinter.ip}</p>
                            <p><span className="text-zinc-500">Бренд:</span> {selectedPrinter.vendor.toUpperCase()}</p>
                            {selectedPrinter.model && <p><span className="text-zinc-500">Модель:</span> {selectedPrinter.model}</p>}
                            {selectedPrinter.serial_number && <p><span className="text-zinc-500">S/N:</span> {selectedPrinter.serial_number}</p>}
                        </div>

                        {/* Отображение остатка картриджей / тонеров */}
                        <div className="space-y-2 border-t border-zinc-800 pt-3">
                            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1">Расходные материалы</h4>
                            <div>
                                <div className="flex justify-between text-xs mb-1"><span>Черный (K)</span><span>{selectedPrinter.toner_black}%</span></div>
                                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                                    <div className="bg-zinc-400 h-full" style={{ width: `${selectedPrinter.toner_black}%` }}></div>
                                </div>
                            </div>

                            {/* Проверяем, цветной ли принтер */}
                            {selectedPrinter.toner_cyan !== null && selectedPrinter.toner_cyan !== undefined && (
                                <div className="grid grid-cols-3 gap-2 pt-1">
                                    <div>
                                        <div className="text-[10px] text-cyan-400">C: {selectedPrinter.toner_cyan}%</div>
                                        <div className="w-full bg-zinc-800 h-1.5 rounded-full"><div className="bg-cyan-400 h-full" style={{ width: `${selectedPrinter.toner_cyan}%` }}></div></div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-magenta-400">M: {selectedPrinter.toner_magenta}%</div>
                                        <div className="w-full bg-zinc-800 h-1.5 rounded-full"><div className="bg-fuchsia-400 h-full" style={{ width: `${selectedPrinter.toner_magenta}%` }}></div></div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-yellow-400">Y: {selectedPrinter.toner_yellow}%</div>
                                        <div className="w-full bg-zinc-800 h-1.5 rounded-full"><div className="bg-yellow-400 h-full" style={{ width: `${selectedPrinter.toner_yellow}%` }}></div></div>
                                    </div>
                                </div>
                            )}
                        </div>

                        <button
                            onClick={() => handleRefresh(selectedPrinter.id)}
                            className="w-full mt-4 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded py-1.5 text-xs font-medium transition-colors"
                        >
                            Запросить статус по сети
                        </button>
                    </div>
                )}
            </aside>

            {/* Основной экран интерактивной карты */}
            <main className="flex-1 flex flex-col items-center justify-center p-8 bg-zinc-900 overflow-auto relative">
                {mapUrl ? (
                    <div
                        ref={mapContainerRef}
                        onClick={handleMapClick}
                        className="relative shadow-2xl bg-zinc-800 rounded-lg overflow-hidden border border-zinc-700 select-none cursor-crosshair"
                        style={{ width: "100%", maxWidth: "1200px", aspectRatio: "16/9" }}
                    >
                        {/* Изображение карты */}
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={mapUrl}
                            alt="План офиса"
                            className="w-full h-full object-contain pointer-events-none"
                        />

                        {/* Рендеринг принтеров */}
                        {printers.map((printer) => (
                            <button
                                key={printer.id}
                                className="printer-marker absolute group transform -translate-x-1/2 -translate-y-1/2 p-2 focus:outline-none transition-transform hover:scale-125 z-10"
                                style={{ left: `${printer.x}%`, top: `${printer.y}%` }}
                                onClick={() => setSelectedPrinter(printer)}
                            >
                                {/* Индикатор статуса работы */}
                                <span className={`relative flex h-4 w-4 rounded-full border-2 border-zinc-900 ${printer.status === 'online' ? 'bg-emerald-500' : 'bg-rose-500'}`}>
                  {printer.status === 'online' && (
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  )}
                </span>

                                {/* Всплывающая подсказка над пином */}
                                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 hidden group-hover:block bg-zinc-950 text-white text-[11px] px-2 py-0.5 rounded shadow border border-zinc-700 whitespace-nowrap z-20">
                  {printer.name || printer.ip}
                </span>
                            </button>
                        ))}

                        {/* Временный пин при выборе места на карте */}
                        {clickCoords && (
                            <div
                                className="absolute transform -translate-x-1/2 -translate-y-1/2 h-5 w-5 border-2 border-dashed border-amber-400 bg-amber-400/20 rounded-full animate-pulse"
                                style={{ left: `${clickCoords.x}%`, top: `${clickCoords.y}%` }}
                            />
                        )}
                    </div>
                ) : (
                    <div className="text-center p-12 border-2 border-dashed border-zinc-700 rounded-xl max-w-md">
                        <p className="text-zinc-400 mb-4">План офиса в формате SVG еще не загружен на сервер.</p>
                        <label className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-md font-medium text-sm cursor-pointer transition-colors">
                            Загрузить первую карту
                            <input type="file" accept=".svg" onChange={handleMapUpload} className="hidden" />
                        </label>
                    </div>
                )}
            </main>
        </div>
    );
}