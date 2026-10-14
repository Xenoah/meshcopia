export const base = import.meta.env.BASE_URL.replace(/\/$/, '');
export const local = (url) => {
  const value = new URL(url, 'https://xenoah.github.io');
  return value.pathname + value.search + value.hash;
};
export const bytes = (n) => n < 1024*1024 ? `${(n/1024).toFixed(0)} KB` : `${(n/1024/1024).toFixed(1)} MB`;
export const categoryNames = {furniture:'家具',props:'プロップ',architecture:'建築',technology:'テクノロジー',materials:'マテリアル'};
