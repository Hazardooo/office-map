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

declare global {
    interface Window {
        APP_CONFIG: {
            apiUrl: string;
            pollingInterval: number;
        };
    }
}

export const getBaseUrl = () => {
    if (typeof window !== "undefined") {
        // Динамически подставляем текущий IP/домен сервера, убирая CORS и ошибки конструктора URL
        return `${window.location.origin}/api`;
    }
    return "http://backend:8000/api";
};

export const api = {
    async getPrinters(): Promise<PrinterListResponse> {
        const res = await fetch(`${getBaseUrl()}/printers/`);
        if (!res.ok) throw new Error("Failed to fetch printers");
        return res.json();
    },

    async createPrinter(data: PrinterCreate): Promise<Printer> {
        const res = await fetch(`${getBaseUrl()}/printers/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Error creating printer");
        }
        return res.json();
    },

    async updatePrinter(id: string, data: Partial<Printer>): Promise<Printer> {
        const res = await fetch(`${getBaseUrl()}/printers/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Error updating printer");
        return res.json();
    },

    async deletePrinter(id: string): Promise<void> {
        const res = await fetch(`${getBaseUrl()}/printers/${id}`, {method: "DELETE"});
        if (!res.ok) throw new Error("Error deleting printer");
    },

    async refreshPrinter(id: string): Promise<Printer> {
        const res = await fetch(`${getBaseUrl()}/printers/${id}/refresh`, {method: "POST"});
        if (!res.ok) throw new Error("Error refreshing printer");
        return res.json();
    },

    async uploadMap(file: File): Promise<{ url: string }> {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${getBaseUrl()}/maps/upload`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Failed to upload map");

        const data = await res.json();
        // Браузер сам подставит домен к относительному пути /maps/file/...
        return data;
    },

    async getCurrentMap(): Promise<{ url: string } | null> {
        const res = await fetch(`${getBaseUrl()}/maps/current`);
        if (res.status === 404) return null;
        if (!res.ok) throw new Error("Failed to fetch map");

        const data = await res.json();
        // Возвращаем как есть, Nginx перехватит этот относительный URL
        return data;
    },

    async getCartridges(): Promise<Cartridge[]> {
        const res = await fetch(`${getBaseUrl()}/cartridges/`);
        if (!res.ok) throw new Error("Не удалось загрузить картриджи");
        return res.json();
    },

    async createCartridge(data: CartridgeCreate): Promise<Cartridge> {
        const res = await fetch(`${getBaseUrl()}/cartridges/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Ошибка при добавлении");
        return res.json();
    },

    async updateCartridge(id: string, data: CartridgeUpdate): Promise<Cartridge> {
        const res = await fetch(`${getBaseUrl()}/cartridges/${id}`, {
            method: "PATCH",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Ошибка при обновлении");
        return res.json();
    },

    async deleteCartridge(id: string): Promise<void> {
        const res = await fetch(`${getBaseUrl()}/cartridges/${id}`, {method: "DELETE"});
        if (res.status === 204) return;
        if (!res.ok) throw new Error("Ошибка при удалении");
    }
};