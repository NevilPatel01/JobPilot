"use client";

import { useEffect } from "react";
import { getAuthToken } from "@/lib/api";

export function AuthInit() {
  useEffect(() => {
    getAuthToken();
  }, []);
  return null;
}
