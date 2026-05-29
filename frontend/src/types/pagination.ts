export interface PageMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PagedResponse<T> {
  data: T[]
  meta: PageMeta
}
