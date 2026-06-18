"use client";

import React, { useState, useEffect, useRef } from "react";

interface OfficeMap {
  id: number;
  name: string;
  file_path: string;
  is_active: boolean;
}

interface Printer {
  id: number;
  name: string;
  model: string | null;
  ip_address: string | null;
  status: string;
  toner_black: number;
  toner_cyan: number | null;
  toner_magenta: number | null;
  toner_yellow: number | null;
  x_coordinate: number;
  y_coordinate: number;
}

export default function Home() {
  const [maps, setMaps] = useState<OfficeMap[]>([]);
  const [activeMap, setActiveMap] = useState<OfficeMap | null>(null);
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [selectedPrinter, setSelectedPrinter] = useState<Printer | null>(null);

  // Режимы
  const [isEditMode, setIsEditMode] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [showPrinterModal, setShowPrinterModal] = useState<boolean>(false);

  // Формы
  const [newMapName, setNewMapName] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Координаты для нового клика
  const [clickCoords, setClickCoords] = useState<{
    x: number;
    y: number;
  } | null>(null);

  // Поля формы принтера
  const [printerForm, setPrinterForm] = useState({
    id: null as number | null,
    name: "",
    model: "",
    ip_address: "",
    status: "online",
    toner_black: 100,
    is_color: false,
    toner_cyan: 100,
    toner_magenta: 100,
    toner_yellow: 100,
  });

  const mapContainerRef = useRef<HTMLDivElement>(null);

  // Загрузка карт при старте
  const loadMaps = async () => {
    try {
      const res = await fetch("/api/maps");
      if (res.ok) {
        const data = await res.json();
        setMaps(data);
        const active = data.find((m: OfficeMap) => m.is_active);
        if (active) {
          setActiveMap(active);
          loadPrinters(active.id);
        } else if (data.length > 0) {
          setActiveMap(data[0]);
          loadPrinters(data[0].id);
        }
      }
    } catch (err) {
      console.error("Ошибка загрузки карт:", err);
    }
  };

  // Загрузка принтеров для конкретной карты
  const loadPrinters = async (mapId: number) => {
    try {
      const res = await fetch(`/api/printers?map_id=${mapId}`);
      if (res.ok) {
        const data = await res.json();
        setPrinters(data);
      }
    } catch (err) {
      console.error("Ошибка загрузки принтеров:", err);
    }
  };

  useEffect(() => {
    loadMaps();
  }, []);

  // Переключение активной карты
  const handleSelectMap = async (map: OfficeMap) => {
    try {
      const res = await fetch(`/api/maps/${map.id}/activate`, {
        method: "POST",
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveMap(updated);
        setPrinters([]);
        setSelectedPrinter(null);
        loadPrinters(updated.id);
        // Обновляем список, чтобы поменялись статусы активности
        loadMaps();
      }
    } catch (err) {
      console.error("Ошибка активации карты:", err);
    }
  };

  // Удаление карты
  const handleDeleteMap = async (mapId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (
      !confirm("Вы уверены, что хотите удалить эту карту со всеми принтерами?")
    )
      return;

    try {
      const res = await fetch(`/api/maps/${mapId}`, { method: "DELETE" });
      if (res.ok) {
        if (activeMap?.id === mapId) {
          setActiveMap(null);
          setPrinters([]);
          setSelectedPrinter(null);
        }
        loadMaps();
      }
    } catch (err) {
      console.error("Ошибка удаления карты:", err);
    }
  };

  // Загрузка новой SVG карты
  const handleUploadMapSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !newMapName) {
      alert("Заполните название карты и выберите SVG файл");
      return;
    }

    const formData = new FormData();
    formData.append("name", newMapName);
    formData.append("file", selectedFile);

    try {
      setIsUploading(true);
      const res = await fetch("/api/maps/upload", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const newMap = await res.json();
        setNewMapName("");
        setSelectedFile(null);
        setActiveMap(newMap);
        loadPrinters(newMap.id);
        loadMaps();
      } else {
        const errData = await res.json();
        alert(`Ошибка загрузки: ${errData.detail || "Неизвестная ошибка"}`);
      }
    } catch (err) {
      console.error("Ошибка отправки файла:", err);
    } finally {
      setIsUploading(false);
    }
  };

  // Клик по карте
  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isEditMode || !activeMap) return;

    // Если кликнули именно по маркеру принтера, не создаем новый
    if ((e.target as HTMLElement).closest(".printer-marker")) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    setClickCoords({ x, y });
    setPrinterForm({
      id: null,
      name: "",
      model: "",
      ip_address: "",
      status: "online",
      toner_black: 100,
      is_color: false,
      toner_cyan: 100,
      toner_magenta: 100,
      toner_yellow: 100,
    });
    setShowPrinterModal(true);
  };

  // Клик по существующему маркеру
  const handleMarkerClick = (printer: Printer, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedPrinter(printer);

    if (isEditMode) {
      setClickCoords({ x: printer.x_coordinate, y: printer.y_coordinate });
      setPrinterForm({
        id: printer.id,
        name: printer.name,
        model: printer.model || "",
        ip_address: printer.ip_address || "",
        status: printer.status,
        toner_black: printer.toner_black,
        is_color: printer.toner_cyan !== null,
        toner_cyan: printer.toner_cyan || 100,
        toner_magenta: printer.toner_magenta || 100,
        toner_yellow: printer.toner_yellow || 100,
      });
      setShowPrinterModal(true);
    }
  };

  // Создание или обновление принтера
  const handleSavePrinter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeMap || !clickCoords) return;

    const payload = {
      name: printerForm.name || "Без названия",
      model: printerForm.model || null,
      ip_address: printerForm.ip_address || null,
      status: printerForm.status,
      toner_black: Number(printerForm.toner_black),
      toner_cyan: printerForm.is_color ? Number(printerForm.toner_cyan) : null,
      toner_magenta: printerForm.is_color
        ? Number(printerForm.toner_magenta)
        : null,
      toner_yellow: printerForm.is_color
        ? Number(printerForm.toner_yellow)
        : null,
      x_coordinate: clickCoords.x,
      y_coordinate: clickCoords.y,
    };

    try {
      let res;
      if (printerForm.id) {
        // Редактирование
        res = await fetch(`/api/printers/${printerForm.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        // Создание нового
        res = await fetch("/api/printers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }

      if (res.ok) {
        const savedPrinter = await res.json();
        setShowPrinterModal(false);
        setClickCoords(null);
        setSelectedPrinter(savedPrinter);
        loadPrinters(activeMap.id);
      }
    } catch (err) {
      console.error("Ошибка сохранения принтера:", err);
    }
  };

  // Удаление принтера
  const handleDeletePrinter = async (printerId: number) => {
    if (!confirm("Вы уверены, что хотите удалить этот принтер?")) return;

    try {
      const res = await fetch(`/api/printers/${printerId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setShowPrinterModal(false);
        setClickCoords(null);
        setSelectedPrinter(null);
        if (activeMap) loadPrinters(activeMap.id);
      }
    } catch (err) {
      console.error("Ошибка удаления принтера:", err);
    }
  };

  // Цвета статуса принтеров
  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "#10b981"; // Green
      case "low_toner":
        return "#f59e0b"; // Orange
      case "no_paper":
        return "#3b82f6"; // Blue
      case "offline":
        return "#9ca3af"; // Gray
      default:
        return "#ef4444"; // Red
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "online":
        return "В сети";
      case "low_toner":
        return "Мало тонера";
      case "no_paper":
        return "Нет бумаги";
      case "offline":
        return "Вне сети";
      default:
        return "Ошибка";
    }
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
        fontFamily: "sans-serif",
        color: "#1f2937",
      }}
    >
      {/* Боковая панель (Управление картами и список принтеров) */}
      <aside
        style={{
          width: "320px",
          borderRight: "1px solid #e5e7eb",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#ffffff",
          flexShrink: 0,
        }}
      >
        {/* Заголовок */}
        <div
          style={{
            padding: "1.2rem",
            borderBottom: "1px solid #e5e7eb",
            backgroundColor: "#3b82f6",
            color: "#ffffff",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "1.4rem" }}>Карта Офиса 🗺️</h1>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.8rem", opacity: 0.9 }}>
            Для системных администраторов
          </p>
        </div>

        {/* Список карт */}
        <div style={{ padding: "1rem", borderBottom: "1px solid #e5e7eb" }}>
          <h3
            style={{
              margin: "0 0 0.8rem 0",
              fontSize: "0.9rem",
              color: "#4b5563",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Карты кабинетов
          </h3>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.4rem",
              maxHeight: "160px",
              overflowY: "auto",
            }}
          >
            {maps.map((m) => (
              <div
                key={m.id}
                onClick={() => handleSelectMap(m)}
                style={{
                  padding: "0.6rem",
                  borderRadius: "6px",
                  backgroundColor:
                    activeMap?.id === m.id ? "#eff6ff" : "#f3f4f6",
                  border:
                    activeMap?.id === m.id
                      ? "1px solid #3b82f6"
                      : "1px solid transparent",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontSize: "0.9rem",
                  fontWeight: activeMap?.id === m.id ? "bold" : "normal",
                }}
              >
                <span
                  style={{
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    maxWidth: "180px",
                  }}
                >
                  {m.name}
                </span>
                <button
                  onClick={(e) => handleDeleteMap(m.id, e)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#ef4444",
                    cursor: "pointer",
                    fontSize: "1.1rem",
                    padding: "0 4px",
                  }}
                  title="Удалить карту"
                >
                  &times;
                </button>
              </div>
            ))}
            {maps.length === 0 && (
              <p
                style={{
                  margin: 0,
                  fontSize: "0.85rem",
                  color: "#9ca3af",
                  textAlign: "center",
                }}
              >
                Нет загруженных карт
              </p>
            )}
          </div>

          {/* Форма загрузки SVG */}
          <form
            onSubmit={handleUploadMapSubmit}
            style={{
              marginTop: "1rem",
              padding: "0.8rem",
              border: "1px dashed #cbd5e1",
              borderRadius: "8px",
            }}
          >
            <h4
              style={{
                margin: "0 0 0.6rem 0",
                fontSize: "0.85rem",
                color: "#4b5563",
              }}
            >
              Загрузить новую карту (SVG)
            </h4>
            <input
              type="text"
              placeholder="Название (например, 3 этаж)"
              value={newMapName}
              onChange={(e) => setNewMapName(e.target.value)}
              style={{
                width: "100%",
                padding: "0.4rem",
                marginBottom: "0.4rem",
                boxSizing: "border-box",
                border: "1px solid #cbd5e1",
                borderRadius: "4px",
                fontSize: "0.8rem",
              }}
              required
            />
            <input
              type="file"
              accept=".svg"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              style={{
                width: "100%",
                fontSize: "0.75rem",
                marginBottom: "0.6rem",
              }}
              required
            />
            <button
              type="submit"
              disabled={isUploading}
              style={{
                width: "100%",
                padding: "0.4rem",
                backgroundColor: "#10b981",
                color: "#ffffff",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: "bold",
              }}
            >
              {isUploading ? "Загрузка..." : "Загрузить карту"}
            </button>
          </form>
        </div>

        {/* Список принтеров на текущей карте */}
        <div
          style={{
            flexGrow: 1,
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
          }}
        >
          <h3
            style={{
              margin: "0 0 0.8rem 0",
              fontSize: "0.9rem",
              color: "#4b5563",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Принтеры на карте ({printers.length})
          </h3>

          <div
            style={{
              flexGrow: 1,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
          >
            {printers.map((p) => (
              <div
                key={p.id}
                onClick={() => setSelectedPrinter(p)}
                style={{
                  padding: "0.6rem",
                  borderRadius: "6px",
                  backgroundColor:
                    selectedPrinter?.id === p.id ? "#f3f4f6" : "#ffffff",
                  border: `1px solid ${selectedPrinter?.id === p.id ? "#9ca3af" : "#e5e7eb"}`,
                  borderLeft: `4px solid ${getStatusColor(p.status)}`,
                  cursor: "pointer",
                  fontSize: "0.85rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontWeight: "bold",
                  }}
                >
                  <span>{p.name}</span>
                  <span
                    style={{
                      color: getStatusColor(p.status),
                      fontSize: "0.75rem",
                    }}
                  >
                    {getStatusText(p.status)}
                  </span>
                </div>
                <div
                  style={{
                    color: "#6b7280",
                    fontSize: "0.75rem",
                    marginTop: "2px",
                  }}
                >
                  {p.model && <div>Модель: {p.model}</div>}
                  {p.ip_address && <div>IP: {p.ip_address}</div>}
                </div>

                {/* Индикатор Тонера */}
                <div style={{ marginTop: "6px" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "0.7rem",
                      color: "#4b5563",
                      marginBottom: "2px",
                    }}
                  >
                    <span>Тонер:</span>
                    <strong>{p.toner_black}%</strong>
                  </div>
                  <div
                    style={{
                      width: "100%",
                      height: "5px",
                      backgroundColor: "#e5e7eb",
                      borderRadius: "3px",
                      overflow: "hidden",
                      display: "flex",
                    }}
                  >
                    {p.toner_cyan !== null ? (
                      <>
                        <div
                          style={{
                            width: "25%",
                            height: "100%",
                            backgroundColor: "#00ffff",
                          }}
                          title={`Cyan: ${p.toner_cyan}%`}
                        />
                        <div
                          style={{
                            width: "25%",
                            height: "100%",
                            backgroundColor: "#ff00ff",
                          }}
                          title={`Magenta: ${p.toner_magenta}%`}
                        />
                        <div
                          style={{
                            width: "25%",
                            height: "100%",
                            backgroundColor: "#ffff00",
                          }}
                          title={`Yellow: ${p.toner_yellow}%`}
                        />
                        <div
                          style={{
                            width: "25%",
                            height: "100%",
                            backgroundColor: "#000000",
                          }}
                          title={`Black: ${p.toner_black}%`}
                        />
                      </>
                    ) : (
                      <div
                        style={{
                          width: `${p.toner_black}%`,
                          height: "100%",
                          backgroundColor: "#111827",
                        }}
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}

            {printers.length === 0 && (
              <p
                style={{
                  margin: "2rem 0",
                  fontSize: "0.85rem",
                  color: "#9ca3af",
                  textAlign: "center",
                }}
              >
                {activeMap
                  ? "Кликните на карту в режиме редактирования, чтобы добавить принтер."
                  : "Загрузите карту, чтобы начать."}
              </p>
            )}
          </div>
        </div>
      </aside>

      {/* Основная область отображения карты */}
      <main
        style={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#f3f4f6",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Панель управления над картой */}
        <div
          style={{
            height: "60px",
            borderBottom: "1px solid #e5e7eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 1.5rem",
            backgroundColor: "#ffffff",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <h2 style={{ margin: 0, fontSize: "1.2rem" }}>
              Текущая карта:{" "}
              <span style={{ color: "#3b82f6" }}>
                {activeMap ? activeMap.name : "Не выбрана"}
              </span>
            </h2>

            {activeMap && (
              <div
                style={{ display: "flex", gap: "0.4rem", fontSize: "0.8rem" }}
              >
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "3px",
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: "#10b981",
                    }}
                  ></span>{" "}
                  В сети
                </span>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "3px",
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: "#f59e0b",
                    }}
                  ></span>{" "}
                  Мало тонера
                </span>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "3px",
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: "#9ca3af",
                    }}
                  ></span>{" "}
                  Вне сети
                </span>
              </div>
            )}
          </div>

          {activeMap && (
            <div style={{ display: "flex", gap: "0.6rem" }}>
              <button
                onClick={() => {
                  setIsEditMode(!isEditMode);
                  setSelectedPrinter(null);
                }}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: isEditMode ? "#ef4444" : "#2563eb",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "0.85rem",
                  fontWeight: "bold",
                  boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                }}
              >
                {isEditMode
                  ? "Закончить редактирование 👁️"
                  : "Режим редактирования 🛠️"}
              </button>
            </div>
          )}
        </div>

        {/* Контейнер карты */}
        <div
          style={{
            flexGrow: 1,
            padding: "2rem",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            overflow: "auto",
            minHeight: 0,
          }}
        >
          {activeMap ? (
            <div
              ref={mapContainerRef}
              onClick={handleMapClick}
              style={{
                position: "relative",
                maxWidth: "100%",
                maxHeight: "100%",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                borderRadius: "8px",
                overflow: "hidden",
                backgroundColor: "#ffffff",
                cursor: isEditMode ? "crosshair" : "default",
                display: "inline-block",
              }}
            >
              {/* Рендерим SVG как изображение */}
              {/* Префикс /api/ благодаря Nginx проксирует запрос на FastAPI StaticFiles */}
              <img
                src={`/api/${activeMap.file_path}`}
                alt={activeMap.name}
                style={{
                  display: "block",
                  maxWidth: "100%",
                  height: "auto",
                  pointerEvents: "none",
                }}
              />

              {/* Маркеры принтеров */}
              {printers.map((p) => (
                <div
                  key={p.id}
                  className="printer-marker"
                  onClick={(e) => handleMarkerClick(p, e)}
                  style={{
                    position: "absolute",
                    left: `${p.x_coordinate}%`,
                    top: `${p.y_coordinate}%`,
                    transform: "translate(-50%, -50%)",
                    width: selectedPrinter?.id === p.id ? "28px" : "22px",
                    height: selectedPrinter?.id === p.id ? "28px" : "22px",
                    borderRadius: "50%",
                    backgroundColor: getStatusColor(p.status),
                    border: `3px solid ${selectedPrinter?.id === p.id ? "#1e3a8a" : "#ffffff"}`,
                    boxShadow: "0 2px 5px rgba(0,0,0,0.3)",
                    cursor: "pointer",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    color: "#ffffff",
                    fontSize: "10px",
                    fontWeight: "bold",
                    transition: "all 0.15s ease-in-out",
                    zIndex: selectedPrinter?.id === p.id ? 10 : 5,
                  }}
                  title={`${p.name} (${p.model || "Принтер"})`}
                >
                  🖨️
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                textAlign: "center",
                padding: "3rem",
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                maxWidth: "450px",
              }}
            >
              <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>🗺️</div>
              <h3 style={{ margin: "0 0 0.5rem 0" }}>
                Добро пожаловать в Карту Офиса!
              </h3>
              <p
                style={{
                  color: "#6b7280",
                  fontSize: "0.9rem",
                  margin: "0 0 1.5rem 0",
                  lineHeight: "1.4",
                }}
              >
                Для начала работы загрузите SVG-файл планировки вашего офиса с
                помощью формы в левой панели.
              </p>
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "#9ca3af",
                  backgroundColor: "#f9fafb",
                  padding: "0.8rem",
                  borderRadius: "6px",
                  border: "1px solid #e5e7eb",
                }}
              >
                💡 Вы можете использовать файл <code>office.svg</code>, который
                уже находится в вашей папке фронтенда!
              </div>
            </div>
          )}
        </div>

        {/* Панель детальной информации о выбранном принтере (Внизу справа) */}
        {selectedPrinter && !isEditMode && (
          <div
            style={{
              position: "absolute",
              bottom: "20px",
              right: "20px",
              width: "320px",
              backgroundColor: "#ffffff",
              borderRadius: "10px",
              boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.15)",
              border: "1px solid #e5e7eb",
              overflow: "hidden",
              zIndex: 20,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.8rem 1rem",
                borderBottom: "1px solid #e5e7eb",
                backgroundColor: "#f8fafc",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "1rem" }}>Детали принтера</h3>
              <button
                onClick={() => setSelectedPrinter(null)}
                style={{
                  background: "none",
                  border: "none",
                  fontSize: "1.2rem",
                  cursor: "pointer",
                  color: "#9ca3af",
                }}
              >
                &times;
              </button>
            </div>

            <div style={{ padding: "1rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "8px",
                }}
              >
                <span style={{ fontSize: "1.4rem" }}>🖨️</span>
                <div>
                  <h4 style={{ margin: 0, fontSize: "1.05rem" }}>
                    {selectedPrinter.name}
                  </h4>
                  <p
                    style={{ margin: 0, color: "#6b7280", fontSize: "0.8rem" }}
                  >
                    {selectedPrinter.model || "Модель не указана"}
                  </p>
                </div>
              </div>

              <hr
                style={{
                  border: "none",
                  borderTop: "1px solid #f1f5f9",
                  margin: "12px 0",
                }}
              />

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  fontSize: "0.85rem",
                }}
              >
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <span style={{ color: "#6b7280" }}>IP-адрес:</span>
                  <strong style={{ fontFamily: "monospace" }}>
                    {selectedPrinter.ip_address || "Не задан"}
                  </strong>
                </div>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <span style={{ color: "#6b7280" }}>Статус связи:</span>
                  <strong
                    style={{ color: getStatusColor(selectedPrinter.status) }}
                  >
                    {getStatusText(selectedPrinter.status)}
                  </strong>
                </div>
              </div>

              <hr
                style={{
                  border: "none",
                  borderTop: "1px solid #f1f5f9",
                  margin: "12px 0",
                }}
              />

              {/* Расширенная панель тонеров */}
              <div>
                <h5 style={{ margin: "0 0 8px 0", fontSize: "0.85rem" }}>
                  Состояние картриджей:
                </h5>
                {selectedPrinter.toner_cyan !== null ? (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    {/* CMYK */}
                    <TonerBar
                      label="Cyan (Голубой)"
                      percent={selectedPrinter.toner_cyan}
                      color="#00ffff"
                    />
                    <TonerBar
                      label="Magenta (Пурпурный)"
                      percent={selectedPrinter.toner_magenta || 0}
                      color="#ff00ff"
                    />
                    <TonerBar
                      label="Yellow (Желтый)"
                      percent={selectedPrinter.toner_yellow || 0}
                      color="#eab308"
                    />
                    <TonerBar
                      label="Black (Черный)"
                      percent={selectedPrinter.toner_black}
                      color="#000000"
                    />
                  </div>
                ) : (
                  <TonerBar
                    label="Черный картридж"
                    percent={selectedPrinter.toner_black}
                    color="#111827"
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Модальное окно добавления/редактирования принтера */}
      {showPrinterModal && clickCoords && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 100,
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "10px",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
              width: "450px",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "1rem 1.5rem",
                borderBottom: "1px solid #e5e7eb",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "1.2rem" }}>
                {printerForm.id
                  ? "Редактировать принтер"
                  : "Добавить новый принтер"}
              </h3>
              <button
                onClick={() => {
                  setShowPrinterModal(false);
                  setClickCoords(null);
                }}
                style={{
                  background: "none",
                  border: "none",
                  fontSize: "1.5rem",
                  cursor: "pointer",
                  color: "#9ca3af",
                }}
              >
                &times;
              </button>
            </div>

            <form
              onSubmit={handleSavePrinter}
              style={{
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.85rem",
                    fontWeight: "bold",
                    marginBottom: "0.3rem",
                  }}
                >
                  Название локации / кабинета
                </label>
                <input
                  type="text"
                  value={printerForm.name}
                  onChange={(e) =>
                    setPrinterForm({ ...printerForm, name: e.target.value })
                  }
                  placeholder="Пример: Бухгалтерия (у окна)"
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    boxSizing: "border-box",
                    border: "1px solid #cbd5e1",
                    borderRadius: "6px",
                  }}
                  required
                />
              </div>

              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ flex: 1 }}>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      fontWeight: "bold",
                      marginBottom: "0.3rem",
                    }}
                  >
                    Модель принтера
                  </label>
                  <input
                    type="text"
                    value={printerForm.model}
                    onChange={(e) =>
                      setPrinterForm({ ...printerForm, model: e.target.value })
                    }
                    placeholder="Kyocera M2040dn"
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      boxSizing: "border-box",
                      border: "1px solid #cbd5e1",
                      borderRadius: "6px",
                    }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      fontWeight: "bold",
                      marginBottom: "0.3rem",
                    }}
                  >
                    IP-адрес
                  </label>
                  <input
                    type="text"
                    value={printerForm.ip_address}
                    onChange={(e) =>
                      setPrinterForm({
                        ...printerForm,
                        ip_address: e.target.value,
                      })
                    }
                    placeholder="192.168.1.150"
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      boxSizing: "border-box",
                      border: "1px solid #cbd5e1",
                      borderRadius: "6px",
                    }}
                  />
                </div>
              </div>

              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ flex: 1 }}>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      fontWeight: "bold",
                      marginBottom: "0.3rem",
                    }}
                  >
                    Текущий статус
                  </label>
                  <select
                    value={printerForm.status}
                    onChange={(e) =>
                      setPrinterForm({ ...printerForm, status: e.target.value })
                    }
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      boxSizing: "border-box",
                      border: "1px solid #cbd5e1",
                      borderRadius: "6px",
                      backgroundColor: "#ffffff",
                    }}
                  >
                    <option value="online">В сети</option>
                    <option value="low_toner">Мало тонера</option>
                    <option value="no_paper">Нет бумаги</option>
                    <option value="offline">Вне сети</option>
                    <option value="error">Ошибка связи</option>
                  </select>
                </div>

                <div
                  style={{
                    flex: 1,
                    display: "flex",
                    alignItems: "flex-end",
                    paddingBottom: "0.5rem",
                  }}
                >
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.85rem",
                      fontWeight: "bold",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={printerForm.is_color}
                      onChange={(e) =>
                        setPrinterForm({
                          ...printerForm,
                          is_color: e.target.checked,
                        })
                      }
                    />
                    Цветной принтер
                  </label>
                </div>
              </div>

              {/* Настройки тонера */}
              <div
                style={{
                  border: "1px solid #f1f5f9",
                  backgroundColor: "#f8fafc",
                  padding: "1rem",
                  borderRadius: "8px",
                }}
              >
                <h4 style={{ margin: "0 0 0.8rem 0", fontSize: "0.9rem" }}>
                  Оставшийся уровень тонера (%)
                </h4>

                {printerForm.is_color ? (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.6rem",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                      }}
                    >
                      <span
                        style={{
                          width: "60px",
                          fontSize: "0.8rem",
                          fontWeight: "bold",
                        }}
                      >
                        Cyan:
                      </span>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={printerForm.toner_cyan}
                        onChange={(e) =>
                          setPrinterForm({
                            ...printerForm,
                            toner_cyan: Number(e.target.value),
                          })
                        }
                        style={{ flexGrow: 1 }}
                      />
                      <span
                        style={{
                          width: "35px",
                          fontSize: "0.8rem",
                          textAlign: "right",
                        }}
                      >
                        {printerForm.toner_cyan}%
                      </span>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                      }}
                    >
                      <span
                        style={{
                          width: "60px",
                          fontSize: "0.8rem",
                          fontWeight: "bold",
                        }}
                      >
                        Magenta:
                      </span>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={printerForm.toner_magenta}
                        onChange={(e) =>
                          setPrinterForm({
                            ...printerForm,
                            toner_magenta: Number(e.target.value),
                          })
                        }
                        style={{ flexGrow: 1 }}
                      />
                      <span
                        style={{
                          width: "35px",
                          fontSize: "0.8rem",
                          textAlign: "right",
                        }}
                      >
                        {printerForm.toner_magenta}%
                      </span>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                      }}
                    >
                      <span
                        style={{
                          width: "60px",
                          fontSize: "0.8rem",
                          fontWeight: "bold",
                        }}
                      >
                        Yellow:
                      </span>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={printerForm.toner_yellow}
                        onChange={(e) =>
                          setPrinterForm({
                            ...printerForm,
                            toner_yellow: Number(e.target.value),
                          })
                        }
                        style={{ flexGrow: 1 }}
                      />
                      <span
                        style={{
                          width: "35px",
                          fontSize: "0.8rem",
                          textAlign: "right",
                        }}
                      >
                        {printerForm.toner_yellow}%
                      </span>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                      }}
                    >
                      <span
                        style={{
                          width: "60px",
                          fontSize: "0.8rem",
                          fontWeight: "bold",
                        }}
                      >
                        Black:
                      </span>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={printerForm.toner_black}
                        onChange={(e) =>
                          setPrinterForm({
                            ...printerForm,
                            toner_black: Number(e.target.value),
                          })
                        }
                        style={{ flexGrow: 1 }}
                      />
                      <span
                        style={{
                          width: "35px",
                          fontSize: "0.8rem",
                          textAlign: "right",
                        }}
                      >
                        {printerForm.toner_black}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <span
                      style={{
                        width: "60px",
                        fontSize: "0.8rem",
                        fontWeight: "bold",
                      }}
                    >
                      Black:
                    </span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={printerForm.toner_black}
                      onChange={(e) =>
                        setPrinterForm({
                          ...printerForm,
                          toner_black: Number(e.target.value),
                        })
                      }
                      style={{ flexGrow: 1 }}
                    />
                    <span
                      style={{
                        width: "35px",
                        fontSize: "0.8rem",
                        textAlign: "right",
                      }}
                    >
                      {printerForm.toner_black}%
                    </span>
                  </div>
                )}
              </div>

              {/* Управление координатами */}
              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                📍 Координаты размещения: X: {clickCoords.x.toFixed(1)}%, Y:{" "}
                {clickCoords.y.toFixed(1)}%
              </div>

              {/* Кнопки */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: "1rem",
                }}
              >
                {printerForm.id ? (
                  <button
                    type="button"
                    onClick={() => handleDeletePrinter(printerForm.id!)}
                    style={{
                      padding: "0.6rem 1.2rem",
                      backgroundColor: "#ef4444",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "6px",
                      cursor: "pointer",
                      fontWeight: "bold",
                      fontSize: "0.85rem",
                    }}
                  >
                    Удалить
                  </button>
                ) : (
                  <div />
                )}

                <div style={{ display: "flex", gap: "0.6rem" }}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowPrinterModal(false);
                      setClickCoords(null);
                    }}
                    style={{
                      padding: "0.6rem 1.2rem",
                      backgroundColor: "#f3f4f6",
                      color: "#4b5563",
                      border: "1px solid #cbd5e1",
                      borderRadius: "6px",
                      cursor: "pointer",
                      fontSize: "0.85rem",
                    }}
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: "0.6rem 1.2rem",
                      backgroundColor: "#10b981",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "6px",
                      cursor: "pointer",
                      fontWeight: "bold",
                      fontSize: "0.85rem",
                    }}
                  >
                    Сохранить
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function TonerBar({
  label,
  percent,
  color,
}: {
  label: string;
  percent: number;
  color: string;
}) {
  const isYellow = color === "#eab308" || color === "#ffff00";
  return (
    <div style={{ fontSize: "0.8rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "3px",
        }}
      >
        <span style={{ color: "#4b5563" }}>{label}</span>
        <strong>{percent}%</strong>
      </div>
      <div
        style={{
          width: "100%",
          height: "10px",
          backgroundColor: "#f1f5f9",
          border: "1px solid #cbd5e1",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${percent}%`,
            height: "100%",
            backgroundColor: color,
            boxShadow: isYellow
              ? "none"
              : "inset 0 0 5px rgba(255,255,255,0.2)",
          }}
        />
      </div>
    </div>
  );
}
