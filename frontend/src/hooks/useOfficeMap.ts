// src/hooks/useOfficeMap.ts
import { useState, useEffect, useCallback, useRef } from "react";
import { api, Printer, Cartridge } from "@/service/api";

// --- МОДУЛЬ 1: Управление принтерами ---
function usePrintersData() {
    const [printers, setPrinters] = useState<Printer[]>([]);
    const [totalPrinters, setTotalPrinters] = useState(0);
    const [loading, setLoading] = useState(false);

    const fetchPrinters = useCallback(async (silent = false) => {
        if (!silent) setLoading(true);
        try {
            const data = await api.getPrinters();
            setPrinters(data.printers);
            setTotalPrinters(data.total);
        } catch (error) {
            console.error("Ошибка загрузки принтеров:", error);
        } finally {
            if (!silent) setLoading(false);
        }
    }, []);

    return { printers, totalPrinters, loading, fetchPrinters, setLoading };
}

// --- МОДУЛЬ 2: Управление картриджами ---
function useCartridgesData() {
    const [cartridges, setCartridges] = useState<Cartridge[]>([]);

    const fetchCartridges = useCallback(async () => {
        try {
            const data = await api.getCartridges();
            setCartridges(data);
        } catch (err) {
            console.error("Ошибка загрузки картриджей:", err);
        }
    }, []);

    return { cartridges, fetchCartridges };
}

// --- МОДУЛЬ 3: Управление UI стейтом (карта, клики, выделения) ---
function useMapInteraction() {
    const [mapUrl, setMapUrl] = useState<string | null>(null);
    const [mode, setMode] = useState<"view" | "add" | "move">("view");
    const [selectedPrinterId, setSelectedPrinterId] = useState<string | null>(null);
    const [clickCoords, setClickCoords] = useState<{ x: number; y: number } | null>(null);

    const [selectedCartridgeId, setSelectedCartridgeId] = useState<string | null>(null);
    const [hoveredCartridgeId, setHoveredCartridgeId] = useState<string | null>(null);

    const [isLinking, setIsLinking] = useState(false);
    const [linkingPrinterIds, setLinkingPrinterIds] = useState<string[]>([]);

    const mapContainerRef = useRef<HTMLDivElement>(null);

    const loadCurrentMap = useCallback(async () => {
        try {
            const data = await api.getCurrentMap();
            if (data) setMapUrl(data.url);
        } catch (error) {
            console.error("Ошибка загрузки карты:", error);
        }
    }, []);

    return {
        mapUrl, setMapUrl, mode, setMode,
        selectedPrinterId, setSelectedPrinterId,
        clickCoords, setClickCoords,
        selectedCartridgeId, setSelectedCartridgeId,
        hoveredCartridgeId, setHoveredCartridgeId,
        isLinking, setIsLinking,
        linkingPrinterIds, setLinkingPrinterIds,
        mapContainerRef, loadCurrentMap
    };
}

// --- ГЛАВНЫЙ ОРКЕСТРАТОР ---
export function useOfficeMap() {
    const printerHook = usePrintersData();
    const cartridgeHook = useCartridgesData();
    const mapHook = useMapInteraction();

    const [newPrinter, setNewPrinter] = useState<{ name: string; ip: string; vendor: "hp" | "kyocera" | "canon" }>({
        name: "", ip: "", vendor: "hp"
    });

    // Инициализация и поллинг
    useEffect(() => {
        printerHook.fetchPrinters(false);
        mapHook.loadCurrentMap();
        cartridgeHook.fetchCartridges();

        // Читаем интервал из глобального конфига (если нет, ставим 60 сек по умолчанию)
        const pollingInterval = typeof window !== "undefined" && window.APP_CONFIG?.pollingInterval
            ? window.APP_CONFIG.pollingInterval
            : 60000;

        const intervalId = setInterval(() => {
            printerHook.fetchPrinters(true);
            cartridgeHook.fetchCartridges();
        }, pollingInterval);

        return () => clearInterval(intervalId);
    }, []);

    const selectedPrinter = printerHook.printers.find(p => p.id === mapHook.selectedPrinterId) || null;

    // --- ОБРАБОТЧИКИ СОБЫТИЙ ---
    const handleMapClick = async (e: React.MouseEvent<HTMLDivElement>) => {
        if (!mapHook.mapContainerRef.current || mapHook.isLinking) return;
        const rect = mapHook.mapContainerRef.current.getBoundingClientRect();
        const x = Number(((e.clientX - rect.left) / rect.width * 100).toFixed(2));
        const y = Number(((e.clientY - rect.top) / rect.height * 100).toFixed(2));

        if (mapHook.mode === "move" && selectedPrinter) {
            try {
                await api.updatePrinter(selectedPrinter.id, { x, y });
                mapHook.setMode("view");
                await printerHook.fetchPrinters(true);
            } catch (error) {
                alert("Ошибка при перемещении принтера");
            }
        } else if (mapHook.mode === "view" || mapHook.mode === "add") {
            mapHook.setMode("add");
            mapHook.setClickCoords({ x, y });
            mapHook.setSelectedPrinterId(null);
            mapHook.setSelectedCartridgeId(null);
        }
    };

    const handleCreatePrinter = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!mapHook.clickCoords) return;
        printerHook.setLoading(true);
        try {
            await api.createPrinter({
                name: newPrinter.name, ip: newPrinter.ip, vendor: newPrinter.vendor,
                x: mapHook.clickCoords.x, y: mapHook.clickCoords.y
            });
            mapHook.setMode("view");
            mapHook.setClickCoords(null);
            setNewPrinter({ name: "", ip: "", vendor: "hp" });
            await printerHook.fetchPrinters(true);
        } catch (error: any) {
            alert(error.message || "Ошибка при создании принтера");
        } finally {
            printerHook.setLoading(false);
        }
    };

    const handleSelectPrinter = (printer: Printer) => {
        if (mapHook.isLinking) {
            mapHook.setLinkingPrinterIds(prev =>
                prev.includes(printer.id) ? prev.filter(id => id !== printer.id) : [...prev, printer.id]
            );
            return;
        }
        mapHook.setSelectedPrinterId(printer.id);
        mapHook.setMode("view");
        mapHook.setClickCoords(null);
    };

    // Обертки для API вызовов с авто-обновлением
    const handleRefresh = async (id: string) => { await api.refreshPrinter(id); await printerHook.fetchPrinters(true); };
    const handleDelete = async (id: string) => { await api.deletePrinter(id); mapHook.setSelectedPrinterId(null); await printerHook.fetchPrinters(true); };
    const handleRename = async (id: string, newName: string) => { await api.updatePrinter(id, { name: newName }); await printerHook.fetchPrinters(true); };

    return {
        ...printerHook,
        ...cartridgeHook,
        ...mapHook,
        newPrinter, setNewPrinter,
        selectedPrinter,
        handleMapClick, handleCreatePrinter, handleSelectPrinter,
        handleRefresh, handleDelete, handleRename,
        handleStartMove: () => mapHook.setMode("move"),
        handleCancelMove: () => { mapHook.setMode("view"); mapHook.setClickCoords(null); },
        handleMapUpload: async (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) {
                printerHook.setLoading(true);
                const data = await api.uploadMap(file);
                mapHook.setMapUrl(data.url);
                printerHook.setLoading(false);
            }
        }
    };
}