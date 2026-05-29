export interface PageMeta {
  total: number
  page: number
  page_size: number
  has_next: boolean
  total_pages: number
}

export interface PagedResponse<T> {
  data: T[]
  meta: PageMeta
}
