"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api, Printer, PrinterListResponse } from "@/service/api";

type Mode = "view" | "add" | "move";

export function useOfficeMap() {
    const [printers, setPrinters] = useState<Printer[]>([]);
    const [totalPrinters, setTotalPrinters] = useState(0);
    const [mapUrl, setMapUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [clickCoords, setClickCoords] = useState<{ x: number; y: number } | null>(null);
    const [selectedPrinter, setSelectedPrinter] = useState<Printer | null>(null);
    const [mode, setMode] = useState<Mode>("view");

    const [newPrinter, setNewPrinter] = useState({
        name: "",
        ip: "",
        vendor: "hp" as "hp" | "kyocera" | "canon"
    });

    const mapContainerRef = useRef<HTMLDivElement>(null);

    const loadPrinters = useCallback(async (isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const data: PrinterListResponse = await api.getPrinters();
            setPrinters(data.printers);
            setTotalPrinters(data.total);

            setSelectedPrinter(prev => {
                if (!prev) return null;
                const updatedPrinter = data.printers.find(p => p.id === prev.id);
                return updatedPrinter ? updatedPrinter : prev;
            });
        } catch (err) {
            console.error("Ошибка при загрузке принтеров:", err);
        } finally {
            if (!isBackground) setLoading(false);
        }
    }, []);

    const loadCurrentMap = useCallback(async () => {
        try {
            const data = await api.getCurrentMap();
            setMapUrl(data.url);
        } catch (err) {
            console.warn("Карта не найдена");
        }
    }, []);

    useEffect(() => {
        loadPrinters(false);
        loadCurrentMap();

        const FRONTEND_POLL_INTERVAL = 60000;

        const intervalId = setInterval(() => {
            loadPrinters(true);
        }, FRONTEND_POLL_INTERVAL);

        return () => clearInterval(intervalId);
    }, [loadPrinters, loadCurrentMap]);

    const handleRefresh = useCallback(async (id: string) => {
        try {
            const updated = await api.refreshPrinter(id);
            setSelectedPrinter(updated);
            loadPrinters(true);
        } catch (err) {
            alert("Ошибка опроса принтера по SNMP/сеть.");
        }
    }, [loadPrinters]);

    const handleDelete = useCallback(async (id: string) => {
        if (!confirm("Удалить принтер?")) return;
        try {
            await api.deletePrinter(id);
            setSelectedPrinter(null);
            loadPrinters(false);
        } catch (err) {
            alert("Ошибка при удалении принтера.");
        }
    }, [loadPrinters]);

    const handleRename = useCallback(async (id: string, newName: string) => {
        try {
            const updated = await api.updatePrinter(id, { name: newName });
            setSelectedPrinter(updated);
            loadPrinters(true);
        } catch (err) {
            alert("Не удалось переименовать принтер.");
        }
    }, [loadPrinters]);

    const handleMapUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || !e.target.files[0]) return;
        setLoading(true);
        try {
            await api.uploadMap(e.target.files[0]);
            loadCurrentMap();
        } catch (err) {
            alert("Ошибка загрузки карты.");
        } finally {
            setLoading(false);
        }
    };

    // ИСПРАВЛЕННАЯ ФУНКЦИЯ
    const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!mapContainerRef.current) return;
        const rect = mapContainerRef.current.getBoundingClientRect();

        // Вычисляем координаты клика в процентах
        const x = Math.round(((e.clientX - rect.left) / rect.width) * 10000) / 100;
        const y = Math.round(((e.clientY - rect.top) / rect.height) * 10000) / 100;

        if (mode === "move" && selectedPrinter) {
            // Если включен режим перемещения, обновляем координаты текущего принтера
            api.updatePrinter(selectedPrinter.id, { x, y }).then(updated => {
                setSelectedPrinter(updated);
                setMode("view");
                loadPrinters(true);
            });
        } else {
            // Любой другой клик по карте открывает форму добавления нового принтера
            setMode("add");
            setClickCoords({ x, y });
            setSelectedPrinter(null); // Закрываем карточку выбранного принтера, если она открыта
        }
    };

    const handleCreatePrinter = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!clickCoords) return;
        try {
            await api.createPrinter({ ...newPrinter, x: clickCoords.x, y: clickCoords.y });
            setMode("view");
            setClickCoords(null);
            setNewPrinter({ name: "", ip: "", vendor: "hp" });
            loadPrinters(false);
        } catch (err) {
            alert("Ошибка при создании принтера.");
        }
    };

    const handleStartMove = () => setMode("move");
    const handleCancelMove = () => {
        setMode("view");
        setClickCoords(null);
    };

    // === 1. ДОБАВЛЯЕМ ЭТУ ФУНКЦИЮ ===
    const handleSelectPrinter = useCallback((printer: Printer | null) => {
        setSelectedPrinter(printer);
        // Если мы кликнули на принтер — принудительно гасим желтую метку и выходим из режима добавления
        if (printer) {
            setClickCoords(null);
            setMode("view");
        }
    }, []);

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
        setNewPrinter,
        setClickCoords,
        setSelectedPrinter,
        setMode,
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