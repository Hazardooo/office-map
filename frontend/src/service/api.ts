const BASE_URL = "http://localhost:8000/api";

export interface Printer {
    id: string;
    name: string;
    ip: string;
    vendor: "hp" | "kyocera" | "canon";
    model?: string;
    x: number;
    y: number;
    toner_black: number;
    toner_cyan?: number;
    toner_magenta?: number;
    toner_yellow?: number;
    is_online: boolean;
}

export interface PrinterCreate {
    name: string;
    ip: string;
    vendor: string;
    x: number;
    y: number;
}

export interface PrinterListResponse {
    total: number;
    printers: Printer[];
}

// === ИНТЕРФЕЙСЫ ДЛЯ КАРТРИДЖЕВ ===
export interface Cartridge {
    id: string;
    name: string;
    color: string;
    quantity: number;
    shop_link?: string | null;
    printer_ids: string[];
}

export interface CartridgeCreate {
    name: string;
    color: string;
    quantity: number;
    shop_link?: string | null;
    printer_ids: string[];
}

export interface CartridgeUpdate {
    name?: string;
    color?: string;
    quantity?: number;
    shop_link?: string | null;
    printer_ids?: string[];
}

export const api = {
    // --- ПРИНТЕРЫ ---
    async getPrinters(): Promise<PrinterListResponse> {
        const res = await fetch(`${BASE_URL}/printers/`);
        if (!res.ok) throw new Error("Failed to fetch printers");
        return res.json();
    },

    async createPrinter(data: PrinterCreate): Promise<Printer> {
        const res = await fetch(`${BASE_URL}/printers/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Error creating printer");
        }
        return res.json();
    },

    async updatePrinter(id: string, data: Partial<Printer>): Promise<Printer> {
        const res = await fetch(`${BASE_URL}/printers/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Error updating printer");
        return res.json();
    },

    async deletePrinter(id: string): Promise<void> {
        const res = await fetch(`${BASE_URL}/printers/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("Error deleting printer");
    },

    async refreshPrinter(id: string): Promise<Printer> {
        const res = await fetch(`${BASE_URL}/printers/${id}/refresh`, { method: "POST" });
        if (!res.ok) throw new Error("Error refreshing printer");
        return res.json();
    },

    // --- КАРТЫ ---
    async uploadMap(file: File): Promise<{ url: string }> {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${BASE_URL}/maps/upload`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Failed to upload map");

        const data = await res.json();
        // Извлекаем "http://localhost:8000" из BASE_URL и приклеиваем к пути
        const backendOrigin = new URL(BASE_URL).origin;
        data.url = data.url.startsWith('http') ? data.url : `${backendOrigin}${data.url}`;

        return data;
    },

    async getCurrentMap(): Promise<{ url: string } | null> {
        const res = await fetch(`${BASE_URL}/maps/current`);
        if (res.status === 404) return null;
        if (!res.ok) throw new Error("Failed to fetch map");

        const data = await res.json();
        // Извлекаем "http://localhost:8000" из BASE_URL и приклеиваем к пути
        const backendOrigin = new URL(BASE_URL).origin;
        data.url = data.url.startsWith('http') ? data.url : `${backendOrigin}${data.url}`;

        return data;
    },
    // --- КАРТРИДЖИ ---
    async getCartridges(): Promise<Cartridge[]> {
        const res = await fetch(`${BASE_URL}/cartridges/`);
        if (!res.ok) throw new Error("Не удалось загрузить картриджи");
        return res.json();
    },

    async createCartridge(data: CartridgeCreate): Promise<Cartridge> {
        const res = await fetch(`${BASE_URL}/cartridges/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Ошибка при добавлении");
        return res.json();
    },

    async updateCartridge(id: string, data: CartridgeUpdate): Promise<Cartridge> {
        const res = await fetch(`${BASE_URL}/cartridges/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Ошибка при обновлении");
        return res.json();
    },

    async deleteCartridge(id: string): Promise<void> {
        const res = await fetch(`${BASE_URL}/cartridges/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("Ошибка при удалении");
    }
};