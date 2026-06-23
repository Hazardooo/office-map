// src/hooks/useOfficeMap.ts
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api, Printer, BASE_URL, PrinterListResponse } from "@/lib/api";

export function useOfficeMap() {
    const [printers, setPrinters] = useState<Printer[]>([]);
    const [totalPrinters, setTotalPrinters] = useState(0);
    const [mapUrl, setMapUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [clickCoords, setClickCoords] = useState<{ x: number; y: number } | null>(null);
    const [selectedPrinter, setSelectedPrinter] = useState<Printer | null>(null);

    const [newPrinter, setNewPrinter] = useState({
        name: "",
        ip: "",
        vendor: "hp" as "hp" | "kyocera" | "canon"
    });

    const mapContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadPrinters();
        loadCurrentMap();
    }, []);

    const loadPrinters = async () => {
        try {
            const data: PrinterListResponse = await api.getPrinters();
            setPrinters(data.printers);
            setTotalPrinters(data.total);
        } catch (err) {
            console.error("Ошибка загрузки списка принтеров:", err);
        }
    };

    const loadCurrentMap = async () => {
        try {
            const data = await api.getCurrentMap();
            setMapUrl(`${BASE_URL}${data.url}`);
        } catch (err) {
            console.log("Карта на бэкенде пока не установлена.");
            setMapUrl(null);
        }
    };

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

    const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!mapContainerRef.current) return;
        if ((e.target as HTMLElement).closest(".printer-marker")) return;

        const rect = mapContainerRef.current.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        setClickCoords({ x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100 });
        setSelectedPrinter(null);
    };

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

    const handleRefresh = useCallback(async (id: string) => {
        try {
            const updated = await api.refreshPrinter(id);
            setSelectedPrinter(updated);
            loadPrinters();
        } catch (err) {
            alert("Ошибка опроса принтера по SNMP/сеть.");
        }
    }, []);

    const handleDelete = useCallback(async (id: string) => {
        if (!confirm("Удалить принтер?")) return;
        try {
            await api.deletePrinter(id);
            setSelectedPrinter(null);
            loadPrinters();
        } catch (err) {
            alert("Ошибка при удалении принтера.");
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
        mapContainerRef,
        setNewPrinter,
        setClickCoords,
        setSelectedPrinter,
        handleMapUpload,
        handleMapClick,
        handleCreatePrinter,
        handleRefresh,
        handleDelete,
    };
}