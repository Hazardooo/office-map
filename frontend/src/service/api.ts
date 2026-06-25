export const BASE_URL = "http://localhost:8000";

export interface Printer {
    id: string;
    name: string;
    ip: string;
    vendor: "kyocera" | "canon" | "hp";
    model?: string | null;
    x: number;
    y: number;
    toner_black: number;
    toner_cyan?: number | null;
    toner_magenta?: number | null;
    toner_yellow?: number | null;
    is_online: boolean;
}

export interface PrinterListResponse {
    total: number;
    printers: Printer[];
}

export interface PrinterCreate {
    ip: string;
    vendor: "kyocera" | "canon" | "hp";
    x: number;
    y: number;
    name?: string | null;
}

export interface PrinterUpdate {
    name?: string | null;
    model?: string | null;
    x?: number | null;
    y?: number | null;
    status?: string | null;
}

export const api = {
    async getPrinters(): Promise<PrinterListResponse> {
        const res = await fetch(`${BASE_URL}/printers/`);
        if (!res.ok) throw new Error("Не удалось загрузить принтеры");
        return res.json();
    },

    async createPrinter(data: PrinterCreate): Promise<Printer> {
        const res = await fetch(`${BASE_URL}/printers/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Ошибка при создании принтера");
        return res.json();
    },

    async updatePrinter(id: string, data: PrinterUpdate): Promise<Printer> {
        const res = await fetch(`${BASE_URL}/printers/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Ошибка при обновлении принтера");
        return res.json();
    },

    async refreshPrinter(id: string): Promise<Printer> {
        const res = await fetch(`${BASE_URL}/printers/${id}/refresh`, {
            method: "POST",
        });
        if (!res.ok) throw new Error("Ошибка при опросе принтера");
        return res.json();
    },

    async deletePrinter(id: string): Promise<void> {
        const res = await fetch(`${BASE_URL}/printers/${id}`, {
            method: "DELETE",
        });
        if (!res.ok) throw new Error("Ошибка при удалении принтера");
    },

    async getCurrentMap(): Promise<{ url: string }> {
        const res = await fetch(`${BASE_URL}/maps/current`);
        if (!res.ok) throw new Error("Карта отсутствует на сервере");
        return res.json();
    },

    async uploadMap(file: File): Promise<{ url: string }> {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${BASE_URL}/maps/upload`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Ошибка при загрузке карты");
        return res.json();
    }
};