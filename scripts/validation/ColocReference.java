import java.nio.file.*;
import java.util.*;
import net.imglib2.img.array.ArrayImgs;
import net.imglib2.img.array.ArrayImg;
import net.imglib2.type.numeric.real.DoubleType;
import net.imglib2.type.logic.BitType;
import net.imglib2.TwinCursor;
import net.imglib2.view.Views;
import sc.fiji.coloc.algorithms.*;
import sc.fiji.coloc.gadgets.*;
/** Calls the installed Coloc 2 implementation directly, without launching Fiji UI. */
public class ColocReference {
 public static void main(String[] args) throws Exception {
  List<String> lines=Files.readAllLines(Paths.get(args[0]));
  double[] a=new double[lines.size()-1],b=a.clone();boolean[] keep=new boolean[a.length];
  for(int i=1;i<lines.size();i++){String[] row=lines.get(i).split(",");a[i-1]=Double.parseDouble(row[0]);b[i-1]=Double.parseDouble(row[1]);keep[i-1]=Integer.parseInt(row[2])>0;}
  ArrayImg<DoubleType,?> ia=ArrayImgs.doubles(a,a.length),ib=ArrayImgs.doubles(b,b.length);
  ArrayImg<BitType,?> mask=ArrayImgs.bits(a.length);int i=0;for(BitType v:mask)v.set(keep[i++]);
  PearsonsCorrelation<DoubleType> pearson=new PearsonsCorrelation<>();
  double p=pearson.calculatePearsons(ia,ib,mask);
  TwinCursor<DoubleType> cursor=new TwinCursor<>(ia.randomAccess(),ib.randomAccess(),mask.localizingCursor());
  double s=new SpearmanRankCorrelation<DoubleType>().calculateSpearmanRank(cursor);
  cursor.reset();
  MandersColocalization.MandersResults m=new MandersColocalization<DoubleType>().calculateMandersCorrelation(cursor,new DoubleType());
  System.out.println("{\"pcc\":"+p+",\"spearman\":"+s+",\"m1\":"+m.m1+",\"m2\":"+m.m2+"}");
 }
}
