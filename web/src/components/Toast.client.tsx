"use client";

import { X } from "lucide-react";
import { Toast } from "@/hooks/use-toast";

interface ToastDisplayProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export function ToastDisplay({ toasts, onRemove }: ToastDisplayProps) {
  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`rounded-lg px-4 py-3 flex items-center gap-3 text-white shadow-lg animate-in slide-in-from-right ${
            toast.type === "error"
              ? "bg-red-500"
              : toast.type === "success"
                ? "bg-green-500"
                : "bg-blue-500"
          }`}
        >
          <span className="text-sm font-medium">{toast.message}</span>
          <button
            onClick={() => onRemove(toast.id)}
            className="hover:bg-white/20 rounded p-0.5"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
