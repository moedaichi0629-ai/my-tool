export interface ShopSummary {
  placeId: string;
  name: string;
  address: string;
  phoneNumber: string | null;
  openingHours: string[] | null;
  rating: number | null;
  mapUrl: string | null;
  website: string | null;
}

export interface GeneratedSite {
  catchCopy: string;
  introduction: string;
  reasons: string;
  services: string;
  businessHours: string;
  access: string;
  contactCta: string;
}
