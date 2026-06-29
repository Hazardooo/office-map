import { useState, useEffect, useCallback, useRef } from "react";
import { api, Printer, Cartridge } from "@/service/api";

export function useOfficeMap() {
    const [printers, setPrinters] = useState<Printer[]>([]);
    const [totalPrinters, setTotalPrinters] = useState(0);
    const [mapUrl, setMapUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Картриджи
    const [cartridges, setCartridges] = useState<Cartridge[]>([]);
    const [selectedCartridgeId, setSelectedCartridgeId] = useState<string | null>(null);

    // НОВЫЕ СТЕЙТЫ ДЛЯ ИНТЕРАКТИВНОСТИ НА КАРТЕ
    const [hoveredCartridgeId, setHoveredCartridgeId] = useState<string | null>(null);
    const [isLinking, setIsLinking] = useState(false);
    const [linkingPrinterIds, setLinkingPrinterIds] = useState<string[]>([]);

    const [mode, setMode] = useState<"view" | "add" | "move">("view");
    const [selectedPrinter, setSelectedPrinter] = useState<Printer | null>(null);
    const [clickCoords, setClickCoords] = useState<{ x: number; y: number } | null>(null);
    const [newPrinter, setNewPrinter] = useState<{ name: string; ip: string; vendor: "hp" | "kyocera" | "canon" }>({
        name: "",
        ip: "",
        vendor: "hp"
    });

    const mapContainerRef = useRef<HTMLDivElement>(null);

    const loadPrinters = useCallback(async (silent = false) => {
        if (!silent) setLoading(true);
        try {
            const data = await api.getPrinters();
            setPrinters(data.printers);
            setTotalPrinters(data.total);

            setSelectedPrinter(prev => {
                if (!prev) return null;
                const updated = data.printers.find(p => p.id === prev.id);
                return updated || prev;
            });
        } catch (error) {
            console.error("Ошибка загрузки принтеров:", error);
        } finally {
            if (!silent) setLoading(false);
        }
    }, []);

    const loadCurrentMap = useCallback(async () => {
        try {
            const data = await api.getCurrentMap();
            if (data) setMapUrl(data.url);
        } catch (error) {
            console.error("Ошибка загрузки карты:", error);
        }
    }, []);

    const loadCartridges = useCallback(async () => {
        try {
            const data = await api.getCartridges();
            setCartridges(data);
        } catch (err) {
            console.error("Ошибка загрузки картриджей:", err);
        }
    }, []);

    useEffect(() => {
        loadPrinters(false);
        loadCurrentMap();
        loadCartridges();

        const FRONTEND_POLL_INTERVAL = 60000;
        const intervalId = setInterval(() => {
            loadPrinters(true);
            loadCartridges();
        }, FRONTEND_POLL_INTERVAL);

        return () => clearInterval(intervalId);
    }, [loadPrinters, loadCurrentMap, loadCartridges]);

    const handleMapUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setLoading(true);
        try {
            const data = await api.uploadMap(file);
            setMapUrl(data.url);
        } catch (error) {
            alert("Ошибка при загрузке карты");
        } finally {
            setLoading(false);
        }
    };

    const handleMapClick = async (e: React.MouseEvent<HTMLDivElement>) => {
        if (!mapContainerRef.current || isLinking) return; // Блокируем создание точек, если мы связываем принтеры
        const rect = mapContainerRef.current.getBoundingClientRect();
        const x = Number(((e.clientX - rect.left) / rect.width * 100).toFixed(2));
        const y = Number(((e.clientY - rect.top) / rect.height * 100).toFixed(2));

        if (mode === "move" && selectedPrinter) {
            try {
                await api.updatePrinter(selectedPrinter.id, { x, y });
                setMode("view");
                await loadPrinters(true);
            } catch (error) {
                alert("Ошибка при перемещении принтера");
            }
        } else if (mode === "view" || mode === "add") {
            setMode("add");
            setClickCoords({ x, y });
            setSelectedPrinter(null);
            setSelectedCartridgeId(null);
        }
    };

    const handleCreatePrinter = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!clickCoords) return;
        setLoading(true);
        try {
            await api.createPrinter({
                name: newPrinter.name,
                ip: newPrinter.ip,
                vendor: newPrinter.vendor,
                x: clickCoords.x,
                y: clickCoords.y
            });
            setMode("view");
            setClickCoords(null);
            setNewPrinter({ name: "", ip: "", vendor: "hp" });
            await loadPrinters(true);
        } catch (error: any) {
            alert(error.message || "Ошибка при создании принтера");
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async (id: string) => {
        try {
            await api.refreshPrinter(id);
            await loadPrinters(true);
        } catch (error) {
            alert("Ошибка при опросе принтера");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Вы уверены, что хотите удалить этот принтер?")) return;
        try {
            await api.deletePrinter(id);
            setSelectedPrinter(null);
            await loadPrinters(true);
        } catch (error) {
            alert("Ошибка при удалении");
        }
    };

    const handleStartMove = () => setMode("move");
    const handleCancelMove = () => {
        setMode("view");
        setClickCoords(null);
    };

    const handleRename = async (id: string, newName: string) => {
        try {
            await api.updatePrinter(id, { name: newName });
            await loadPrinters(true);
        } catch (error) {
            alert("Ошибка при переименовании");
        }
    };

    const handleSelectPrinter = (printer: Printer) => {
        if (isLinking) {
            // Режим связывания: клик по принтеру добавляет/удаляет его из массива
            setLinkingPrinterIds(prev =>
                prev.includes(printer.id)
                    ? prev.filter(id => id !== printer.id)
                    : [...prev, printer.id]
            );
            return;
        }

        setSelectedPrinter(printer);
        setMode("view");
        setClickCoords(null);
    };

    return {
        printers,
        totalPrinters,
        mapUrl,
        loading,
        clickCoords,
        newPrinter,
        selectedPrinter,
        mode,
        mapContainerRef,
        cartridges,
        selectedCartridgeId,
        hoveredCartridgeId,
        isLinking,
        linkingPrinterIds,
        setHoveredCartridgeId,
        setIsLinking,
        setLinkingPrinterIds,
        setSelectedCartridgeId,
        loadCartridges,
        setNewPrinter,
        setClickCoords,
        setSelectedPrinter,
        handleMapUpload,
        handleMapClick,
        handleCreatePrinter,
        handleRefresh,
        handleDelete,
        handleStartMove,
        handleCancelMove,
        handleRename,
        handleSelectPrinter
    };
}