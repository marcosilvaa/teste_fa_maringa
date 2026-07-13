-- Filtro Lua para Quarto/Pandoc:
-- 1. Força quebra de texto em todas as colunas (l → p{width})
-- 2. Tabelas com 13+ colunas → página em paisagem + scriptsize
-- 3. Tabelas com 9-12 colunas → \small + colsep reduzido

local THRESHOLD_LANDSCAPE = 13
local THRESHOLD_SMALL = 9  -- nao usado apos split, mantido como seguranca

function Table(el)
  local ncols = 0
  if el.colspecs then
    ncols = #el.colspecs
  end
  if ncols == 0 then return el end

  local w = 1.0 / ncols
  for i = 1, ncols do
    el.colspecs[i][2] = w
  end

  if ncols >= THRESHOLD_LANDSCAPE then
    return pandoc.Blocks({
      pandoc.RawBlock('latex', '\\begin{landscape}\\scriptsize\\setlength{\\tabcolsep}{2pt}\\renewcommand{\\arraystretch}{1.0}'),
      el,
      pandoc.RawBlock('latex', '\\end{landscape}')
    })
  elseif ncols >= THRESHOLD_SMALL then
    return pandoc.Blocks({
      pandoc.RawBlock('latex', '{\\small\\setlength{\\tabcolsep}{3pt}'),
      el,
      pandoc.RawBlock('latex', '}')
    })
  end

  return el
end